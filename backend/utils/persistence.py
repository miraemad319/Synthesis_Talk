import json
import os
import logging
import time
import shutil
from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PersistenceManager:
    """
    Enhanced persistence management with backup, cleanup, and better error handling
    """
    
    def __init__(self, data_file: str = "session_data.json", backup_dir: str = "backups"):
        self.data_file = data_file
        self.backup_dir = backup_dir
        self.lock = threading.Lock()
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure backup directory exists"""
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def _create_backup(self) -> bool:
        """Create a backup of the current data file"""
        if not os.path.exists(self.data_file):
            return True
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.backup_dir, f"session_data_backup_{timestamp}.json")
            shutil.copy2(self.data_file, backup_file)
            logger.info(f"Created backup: {backup_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
    
    def _cleanup_old_backups(self, max_backups: int = 10, max_age_days: int = 30):
        """Clean up old backup files"""
        try:
            if not os.path.exists(self.backup_dir):
                return
            
            backup_files = []
            cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
            
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("session_data_backup_") and filename.endswith(".json"):
                    filepath = os.path.join(self.backup_dir, filename)
                    stat = os.stat(filepath)
                    backup_files.append((filepath, stat.st_mtime))
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Remove files beyond max_backups or older than max_age_days
            for i, (filepath, mtime) in enumerate(backup_files):
                if i >= max_backups or mtime < cutoff_time:
                    try:
                        os.remove(filepath)
                        logger.info(f"Removed old backup: {filepath}")
                    except Exception as e:
                        logger.warning(f"Failed to remove backup {filepath}: {e}")
                        
        except Exception as e:
            logger.error(f"Error during backup cleanup: {e}")
    
    def save_sessions(self, conversations: Dict[str, Any], documents: Dict[str, Any]) -> bool:
        """
        Save session data with enhanced error handling and backup
        
        Args:
            conversations: Dictionary of conversation data
            documents: Dictionary of document data
            
        Returns:
            bool: True if save was successful
        """
        with self.lock:
            try:
                # Validate input data
                if not isinstance(conversations, dict):
                    logger.error("Conversations must be a dictionary")
                    return False
                
                if not isinstance(documents, dict):
                    logger.error("Documents must be a dictionary")
                    return False
                
                # Create backup before overwriting
                self._create_backup()
                
                # Prepare data with metadata
                data = {
                    "conversations": conversations,
                    "documents": {k: v for k, v in documents.items()},
                    "metadata": {
                        "last_saved": datetime.now().isoformat(),
                        "version": "1.0",
                        "conversation_count": len(conversations),
                        "document_count": len(documents)
                    }
                }
                
                # Write to temporary file first
                temp_file = self.data_file + ".tmp"
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                # Move temporary file to actual file (atomic operation)
                shutil.move(temp_file, self.data_file)
                
                logger.info(f"Successfully saved {len(conversations)} conversations and {len(documents)} documents")
                
                # Clean up old backups
                self._cleanup_old_backups()
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to save sessions: {e}")
                # Clean up temporary file if it exists
                temp_file = self.data_file + ".tmp"
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                return False
    
    def load_sessions(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Load session data with enhanced error handling and recovery
        
        Returns:
            Tuple of (conversations, documents)
        """
        with self.lock:
            # Try to load from main file
            if os.path.exists(self.data_file):
                try:
                    with open(self.data_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    # Validate data structure
                    conversations = data.get("conversations", {})
                    documents = data.get("documents", {})
                    metadata = data.get("metadata", {})
                    
                    if not isinstance(conversations, dict):
                        logger.warning("Invalid conversations data, initializing empty")
                        conversations = {}
                    
                    if not isinstance(documents, dict):
                        logger.warning("Invalid documents data, initializing empty")
                        documents = {}
                    
                    logger.info(f"Loaded {len(conversations)} conversations and {len(documents)} documents")
                    if metadata:
                        logger.info(f"Last saved: {metadata.get('last_saved', 'unknown')}")
                    
                    return conversations, documents
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error in main file: {e}")
                except Exception as e:
                    logger.error(f"Error loading main file: {e}")
            
            # Try to recover from backup
            backup_data = self._try_recover_from_backup()
            if backup_data:
                logger.info("Successfully recovered from backup")
                return backup_data
            
            # Return empty data as last resort
            logger.info("No valid data found, starting with empty sessions")
            return {}, {}
    
    def _try_recover_from_backup(self) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """Try to recover data from the most recent backup"""
        try:
            if not os.path.exists(self.backup_dir):
                return None
            
            backup_files = []
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("session_data_backup_") and filename.endswith(".json"):
                    filepath = os.path.join(self.backup_dir, filename)
                    stat = os.stat(filepath)
                    backup_files.append((filepath, stat.st_mtime))
            
            if not backup_files:
                return None
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Try to load from most recent backup
            for filepath, _ in backup_files:
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    conversations = data.get("conversations", {})
                    documents = data.get("documents", {})
                    
                    if isinstance(conversations, dict) and isinstance(documents, dict):
                        logger.info(f"Recovered data from backup: {filepath}")
                        return conversations, documents
                        
                except Exception as e:
                    logger.warning(f"Failed to load backup {filepath}: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error during backup recovery: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about stored data"""
        try:
            conversations, documents = self.load_sessions()
            
            stats = {
                "conversation_count": len(conversations),
                "document_count": len(documents),
                "total_messages": sum(len(conv.get("messages", [])) for conv in conversations.values()),
                "total_document_chunks": sum(len(doc.get("chunks", [])) for doc in documents.values()),
                "data_file_size": os.path.getsize(self.data_file) if os.path.exists(self.data_file) else 0
            }
            
            # Add backup information
            if os.path.exists(self.backup_dir):
                backup_files = [f for f in os.listdir(self.backup_dir) 
                              if f.startswith("session_data_backup_") and f.endswith(".json")]
                stats["backup_count"] = len(backup_files)
            else:
                stats["backup_count"] = 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}

# Global instance for backward compatibility
_global_manager = PersistenceManager()

def save_sessions(conversations: Dict[str, Any], documents: Dict[str, Any]) -> bool:
    """Backward compatible save function"""
    return _global_manager.save_sessions(conversations, documents)

def load_sessions() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Backward compatible load function"""
    return _global_manager.load_sessions()

def get_persistence_stats() -> Dict[str, Any]:
    """Get statistics about stored data"""
    return _global_manager.get_stats()
