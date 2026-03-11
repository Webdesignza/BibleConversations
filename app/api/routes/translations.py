"""
API Routes for Bible Translation Management
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.security import verify_api_key
from app.services.rag_service import get_rag_service

router = APIRouter()


class CreateTranslationRequest(BaseModel):
    translation_id: str
    name: str
    description: Optional[str] = ""


class SwitchTranslationRequest(BaseModel):
    translation_id: str


@router.get("/list")
async def list_translations():  # Remove: api_key: str = Depends(verify_api_key)
    """Get list of all available Bible translations"""
    try:
        rag_service = get_rag_service()
        translations = rag_service.get_available_translations()
        
        return {
            'success': True,
            'translations': translations,
            'count': len(translations)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list translations: {str(e)}"
        )


@router.get("/current")
async def get_current_translation(api_key: str = Depends(verify_api_key)):
    """
    Get the currently active translation
    
    Returns:
        Current translation info or null if none selected
    """
    try:
        rag_service = get_rag_service()
        current = rag_service.get_current_translation()
        
        return {
            'success': True,
            'translation': current
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get current translation: {str(e)}"
        )


@router.post("/create")
async def create_translation(
    request: CreateTranslationRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Create a new Bible translation collection
    
    Args:
        request: Translation ID, name, and description
    
    Returns:
        Success status and message
    """
    try:
        rag_service = get_rag_service()
        result = rag_service.create_translation(
            translation_id=request.translation_id,
            name=request.name,
            description=request.description
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create translation: {str(e)}"
        )


@router.delete("/{translation_id}")
async def delete_translation(
    translation_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Delete a Bible translation and its database
    
    Args:
        translation_id: ID of translation to delete
    
    Returns:
        Success status and message
    """
    try:
        rag_service = get_rag_service()
        result = rag_service.delete_translation(translation_id)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete translation: {str(e)}"
        )

@router.get("/debug")
async def debug_filesystem():
    """Debug filesystem permissions"""
    import os
    from pathlib import Path
    
    chroma_path = Path("./chroma_db")
    translations_file = chroma_path / "translations.json"
    
    debug_info = {
        "chroma_path_exists": chroma_path.exists(),
        "chroma_path_writable": os.access(str(chroma_path), os.W_OK),
        "translations_file_exists": translations_file.exists(),
        "cwd": os.getcwd(),
        "env_chroma_path": os.getenv("CHROMA_DB_PATH", "not set")
    }
    
    # Try to write a test file
    try:
        test_file = chroma_path / "test.txt"
        test_file.write_text("test")
        debug_info["can_write"] = True
        test_file.unlink()
    except Exception as e:
        debug_info["can_write"] = False
        debug_info["write_error"] = str(e)
    
    return debug_info

@router.get("/debug-verse-test")
async def debug_verse_test():
    import chromadb
    try:
        client = chromadb.PersistentClient(path="chroma_db/KJV")
        collection = client.get_collection("langchain")
        
        # Just get first 3 documents and show ALL metadata
        results = collection.get(
            limit=3,
            include=["documents", "metadatas"]
        )
        
        return {
            "sample_metadata": results["metadatas"],
            "sample_docs": [d[:120] for d in results["documents"]]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/debug-chroma")
async def debug_chroma():
    """Debug ChromaDB folder structure"""
    import os
    from pathlib import Path
    
    chroma_path = Path("./chroma_db")
    
    structure = {}
    for trans_folder in chroma_path.iterdir():
        if trans_folder.is_dir():
            structure[trans_folder.name] = [f.name for f in trans_folder.iterdir()]
    
    return {
        "chroma_path_exists": chroma_path.exists(),
        "contents": structure
    }

@router.get("/debug-versions")
async def debug_versions():
    """Debug package versions"""
    import chromadb
    import langchain_chroma
    return {
        "chromadb_version": chromadb.__version__,
        "langchain_chroma_version": langchain_chroma.__version__
    }

@router.get("/debug-collection/{translation_id}")
async def debug_collection(translation_id: str):
    """Debug a specific ChromaDB collection"""
    from pathlib import Path
    from chromadb import PersistentClient
    
    chroma_path = Path("./chroma_db") / translation_id
    
    try:
        client = PersistentClient(path=str(chroma_path))
        collections = client.list_collections()
        
        result = {
            "path": str(chroma_path),
            "path_exists": chroma_path.exists(),
            "collections": []
        }
        
        for col in collections:
            try:
                count = col.count()
                # Try to peek at the collection
                peek = col.peek(limit=1)
                
                result["collections"].append({
                    "name": col.name,
                    "count": count,
                    "metadata": col.metadata,
                    "peek_success": True
                })
            except Exception as e:
                result["collections"].append({
                    "name": col.name,
                    "error": str(e),
                    "peek_success": False
                })
        
        return result
        
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@router.get("/simple-version")
async def simple_version():
    """Ultra simple version check"""
    try:
        import chromadb
        import langchain_chroma
        import sys
        
        # Get langchain_chroma version differently
        try:
            from importlib.metadata import version
            lc_version = version('langchain-chroma')
        except:
            lc_version = "unknown"
        
        return {
            "chromadb": chromadb.__version__,
            "langchain_chroma": lc_version,
            "python": sys.version
        }
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@router.get("/debug-books/{translation_id}")
async def debug_books(translation_id: str):
    """Debug what book names exist in a translation"""
    from pathlib import Path
    from chromadb import PersistentClient
    from chromadb.config import Settings as ChromaSettings
    
    chroma_path = Path("./chroma_db") / translation_id
    
    try:
        client = PersistentClient(
            path=str(chroma_path),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        collections = client.list_collections()
        if not collections:
            return {"error": "No collections found"}
        
        collection = collections[0]
        
        # Get a sample of documents
        results = collection.get(limit=100)
        
        # Extract unique book names
        books = set()
        if results and 'metadatas' in results:
            for meta in results['metadatas']:
                if meta and 'book' in meta:
                    books.add(meta['book'])
        
        return {
            "translation_id": translation_id,
            "collection_name": collection.name,
            "total_documents": collection.count(),
            "unique_books_found": sorted(list(books)),
            "sample_count": len(results['metadatas']) if results and 'metadatas' in results else 0
        }
        
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
    
@router.get("/debug-metadata/{translation_id}")
async def debug_metadata(translation_id: str):
    """Debug actual metadata structure"""
    from pathlib import Path
    from chromadb import PersistentClient
    from chromadb.config import Settings as ChromaSettings
    
    chroma_path = Path("./chroma_db") / translation_id
    
    try:
        client = PersistentClient(
            path=str(chroma_path),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        collections = client.list_collections()
        if not collections:
            return {"error": "No collections found"}
        
        collection = collections[0]
        
        # Get first 5 documents with their full metadata
        results = collection.get(limit=5, include=['metadatas', 'documents'])
        
        samples = []
        if results and 'metadatas' in results:
            for i, meta in enumerate(results['metadatas'][:5]):
                doc_preview = results['documents'][i][:200] if results.get('documents') else "N/A"
                samples.append({
                    "metadata": meta,
                    "document_preview": doc_preview
                })
        
        return {
            "translation_id": translation_id,
            "collection_name": collection.name,
            "total_documents": collection.count(),
            "samples": samples
        }
        
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@router.post("/switch")
async def switch_translation(
    request: SwitchTranslationRequest,
    #REMOVE api_key: str = Depends(verify_api_key)
):
    """
    Switch to a different Bible translation
    
    Args:
        request: Translation ID to switch to
    
    Returns:
        Success status and translation info
    """
    try:
        rag_service = get_rag_service()
        result = rag_service.switch_translation(request.translation_id)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to switch translation: {str(e)}"
        )
    
    