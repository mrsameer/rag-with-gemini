"""RAG Application with Gemini - Complete File Inventory Management."""

import os
import tempfile
import time
from datetime import datetime
from typing import Dict, List, Optional

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types as genai_types

# Load environment variables
load_dotenv()

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FILE_SEARCH_STORE_NAME = os.getenv("FILE_SEARCH_STORE_NAME")
FILE_SEARCH_DISPLAY_NAME = os.getenv("FILE_SEARCH_DISPLAY_NAME", "rag-streamlit-store")

if not GEMINI_API_KEY:
    st.error("GEMINI_API_KEY not found in .env file")
    st.stop()


@st.cache_resource
def init_genai() -> genai.Client:
    """Initialize and cache the Gemini API client."""
    return genai.Client(api_key=GEMINI_API_KEY)


def format_bytes(bytes_value: int) -> str:
    """Format bytes to human-readable string."""
    if bytes_value < 1024:
        return f"{bytes_value} B"
    elif bytes_value < 1024**2:
        return f"{bytes_value / 1024:.2f} KB"
    elif bytes_value < 1024**3:
        return f"{bytes_value / (1024**2):.2f} MB"
    else:
        return f"{bytes_value / (1024**3):.2f} GB"


def format_timestamp(timestamp) -> str:
    """Format RFC 3339 timestamp or datetime object to readable format."""
    try:
        # If already a datetime object, use it directly
        if isinstance(timestamp, datetime):
            return timestamp.strftime("%Y-%m-%d %H:%M:%S")
        # If string, parse it first
        elif isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return str(timestamp)
    except Exception:
        return str(timestamp)


def get_or_create_file_search_store(
    client: genai.Client, display_name: str = FILE_SEARCH_DISPLAY_NAME
) -> str:
    """Get existing or create new File Search store."""
    # Check if store name is in environment
    if FILE_SEARCH_STORE_NAME:
        return FILE_SEARCH_STORE_NAME

    # Check session state
    if "store_name" in st.session_state:
        return st.session_state.store_name

    # Try to find existing store by display name
    try:
        for store in client.file_search_stores.list():
            if store.display_name == display_name:
                st.session_state.store_name = store.name
                return store.name
    except Exception as e:
        st.warning(f"Could not list existing stores: {e}")

    # Create new store
    try:
        store = client.file_search_stores.create(
            config=genai_types.CreateFileSearchStoreConfig(display_name=display_name)
        )
        st.session_state.store_name = store.name
        return store.name
    except Exception as e:
        st.error(f"Failed to create File Search store: {e}")
        st.stop()


def wait_for_operation(
    client: genai.Client, operation, timeout_seconds: int = 300
) -> bool:
    """Wait for operation to complete with progress tracking."""
    deadline = time.time() + timeout_seconds
    current = operation

    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        while not current.done:
            if time.time() >= deadline:
                status_text.error("⏱️ Operation timed out")
                return False

            elapsed = time.time() - (deadline - timeout_seconds)
            progress = min(elapsed / timeout_seconds, 0.99)
            progress_bar.progress(progress)
            status_text.text("Processing document...")

            time.sleep(3)
            current = client.operations.get(current)

        progress_bar.progress(1.0)

        if hasattr(current, "error") and current.error:
            error_msg = getattr(current.error, "message", str(current.error))
            status_text.error(f"❌ Operation failed: {error_msg}")
            return False

        status_text.success("✅ Complete!")
        time.sleep(0.5)
        return True

    finally:
        progress_bar.empty()
        status_text.empty()


def get_store_stats(client: genai.Client, store_name: str) -> Dict:
    """Get comprehensive store statistics."""
    try:
        store = client.file_search_stores.get(name=store_name)

        # Handle None values by defaulting to 0
        active = store.active_documents_count or 0
        pending = store.pending_documents_count or 0
        failed = store.failed_documents_count or 0

        return {
            "name": store.name,
            "display_name": store.display_name,
            "active_documents": active,
            "pending_documents": pending,
            "failed_documents": failed,
            "total_documents": active + pending + failed,
            "size_bytes": store.size_bytes or 0,
            "create_time": store.create_time,
            "update_time": store.update_time,
        }
    except Exception as e:
        st.error(f"Failed to get store stats: {e}")
        return {}


def list_all_stores(client: genai.Client) -> List[Dict]:
    """List all File Search stores."""
    try:
        stores = []
        for store in client.file_search_stores.list():
            # Handle None values by defaulting to 0
            active = store.active_documents_count or 0
            pending = store.pending_documents_count or 0
            failed = store.failed_documents_count or 0

            stores.append(
                {
                    "name": store.name,
                    "display_name": store.display_name,
                    "active_documents": active,
                    "pending_documents": pending,
                    "failed_documents": failed,
                    "total_documents": active + pending + failed,
                    "size_bytes": store.size_bytes or 0,
                    "create_time": store.create_time,
                }
            )
        return stores
    except Exception as e:
        st.error(f"Failed to list stores: {e}")
        return []


def create_store(client: genai.Client, display_name: str) -> Optional[str]:
    """Create a new File Search store."""
    try:
        store = client.file_search_stores.create(
            config=genai_types.CreateFileSearchStoreConfig(display_name=display_name)
        )
        return store.name
    except Exception as e:
        st.error(f"Failed to create store: {e}")
        return None


def delete_store(client: genai.Client, store_name: str, force: bool = True) -> bool:
    """Delete a File Search store."""
    try:
        client.file_search_stores.delete(name=store_name, config={"force": force})
        return True
    except Exception as e:
        st.error(f"Failed to delete store: {e}")
        return False


def upload_document(
    client: genai.Client,
    store_name: str,
    uploaded_file,
    display_name: Optional[str] = None,
    metadata: Optional[Dict] = None,
    chunk_size: int = 400,
    chunk_overlap: int = 40,
) -> bool:
    """Upload a document with custom configuration."""
    temp_path = None
    try:
        # Save to temporary file
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=os.path.splitext(uploaded_file.name)[1]
        ) as tmp:
            tmp.write(uploaded_file.getvalue())
            temp_path = tmp.name

        # Prepare upload config
        config = {
            "chunking_config": {
                "white_space_config": {
                    "max_tokens_per_chunk": chunk_size,
                    "max_overlap_tokens": chunk_overlap,
                }
            }
        }

        if display_name:
            config["display_name"] = display_name

        if metadata:
            config["custom_metadata"] = [
                {"key": k, "string_value": str(v)} for k, v in metadata.items()
            ]

        # Upload to File Search store
        upload_op = client.file_search_stores.upload_to_file_search_store(
            file_search_store_name=store_name,
            file=temp_path,
            config=config,
        )

        return wait_for_operation(client, upload_op)

    except Exception as e:
        st.error(f"Upload failed: {e}")
        return False
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def list_all_documents(client: genai.Client, store_name: str) -> List[Dict]:
    """List all documents with full details and pagination."""
    try:
        documents = []
        # The SDK returns an iterable that handles pagination automatically
        for doc in client.file_search_stores.documents.list(parent=store_name):
            # Extract custom metadata
            custom_meta = {}
            if hasattr(doc, "custom_metadata") and doc.custom_metadata:
                for meta in doc.custom_metadata:
                    if hasattr(meta, "string_value"):
                        custom_meta[meta.key] = meta.string_value
                    elif hasattr(meta, "numeric_value"):
                        custom_meta[meta.key] = meta.numeric_value
                    elif hasattr(meta, "string_list_value"):
                        custom_meta[meta.key] = list(meta.string_list_value.values)

            documents.append(
                {
                    "id": doc.name,
                    "display_name": doc.display_name or os.path.basename(doc.name),
                    "state": doc.state if hasattr(doc, "state") else "UNKNOWN",
                    "size_bytes": doc.size_bytes if hasattr(doc, "size_bytes") else 0,
                    "mime_type": doc.mime_type if hasattr(doc, "mime_type") else "unknown",
                    "create_time": doc.create_time if hasattr(doc, "create_time") else "",
                    "update_time": doc.update_time if hasattr(doc, "update_time") else "",
                    "custom_metadata": custom_meta,
                }
            )

        return documents
    except Exception as e:
        st.error(f"Failed to list documents: {e}")
        return []


def get_document_details(client: genai.Client, doc_id: str) -> Optional[Dict]:
    """Get detailed information about a specific document."""
    try:
        doc = client.file_search_stores.documents.get(name=doc_id)

        # Extract custom metadata
        custom_meta = {}
        if hasattr(doc, "custom_metadata") and doc.custom_metadata:
            for meta in doc.custom_metadata:
                if hasattr(meta, "string_value"):
                    custom_meta[meta.key] = meta.string_value
                elif hasattr(meta, "numeric_value"):
                    custom_meta[meta.key] = meta.numeric_value
                elif hasattr(meta, "string_list_value"):
                    custom_meta[meta.key] = list(meta.string_list_value.values)

        return {
            "id": doc.name,
            "display_name": doc.display_name,
            "state": doc.state,
            "size_bytes": doc.size_bytes,
            "mime_type": doc.mime_type,
            "create_time": doc.create_time,
            "update_time": doc.update_time,
            "custom_metadata": custom_meta,
        }
    except Exception as e:
        st.error(f"Failed to get document details: {e}")
        return None


def delete_document(client: genai.Client, doc_id: str) -> bool:
    """Delete a document from the File Search store."""
    try:
        client.file_search_stores.documents.delete(name=doc_id)
        return True
    except Exception as e:
        st.error(f"Failed to delete document: {e}")
        return False


def extract_citations(response) -> List[str]:
    """Extract citations from Gemini response."""
    citations = []
    try:
        candidate = response.candidates[0] if hasattr(response, "candidates") else None
        grounding_metadata = getattr(candidate, "grounding_metadata", None)

        if grounding_metadata and grounding_metadata.grounding_chunks:
            for chunk in grounding_metadata.grounding_chunks:
                rc = getattr(chunk, "retrieved_context", None)
                if not rc:
                    continue

                if rc.uri:
                    citations.append(rc.uri)
                elif rc.title:
                    citations.append(rc.title)
                elif rc.text:
                    citations.append(rc.text[:80])
    except Exception:
        pass

    return citations


def chat_with_documents(
    client: genai.Client, store_name: str, query: str, use_google_search: bool = False
) -> tuple[Optional[str], List[str]]:
    """Chat using File Search or Google Search."""
    try:
        if use_google_search:
            tools = [genai_types.Tool(google_search=genai_types.GoogleSearch())]
        else:
            tools = [
                genai_types.Tool(
                    file_search=genai_types.FileSearch(
                        file_search_store_names=[store_name]
                    )
                )
            ]

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query,
            config=genai_types.GenerateContentConfig(tools=tools),
        )

        text_response = response.text if response.text else (
            "I couldn't generate a response. Please try rephrasing your question."
        )
        citations = extract_citations(response)

        return text_response, citations

    except Exception as e:
        st.error(f"Chat failed: {e}")
        return None, []


def render_store_analytics(stats: Dict):
    """Render store analytics dashboard."""
    st.subheader("📊 Store Analytics")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Documents", stats.get("total_documents", 0))

    with col2:
        st.metric("Active", stats.get("active_documents", 0))

    with col3:
        st.metric("Pending", stats.get("pending_documents", 0))

    with col4:
        st.metric("Failed", stats.get("failed_documents", 0))

    # Storage usage
    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        size_bytes = stats.get("size_bytes", 0)
        size_gb = size_bytes / (1024**3)
        st.metric("Storage Used", format_bytes(size_bytes))

        # Storage warning
        if size_gb > 15:
            st.warning("⚠️ Approaching 20GB recommended limit")

    with col2:
        if stats.get("create_time"):
            st.metric("Created", format_timestamp(stats["create_time"]))


def render_all_stores_overview(client: genai.Client):
    """Render comprehensive overview of all stores."""
    st.header("🏪 All File Search Stores")

    stores = list_all_stores(client)

    if not stores:
        st.info("No stores found. Create your first store below.")
        return

    # Summary metrics
    total_docs = sum(s["total_documents"] for s in stores)
    total_size = sum(s["size_bytes"] for s in stores)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Stores", len(stores))
    with col2:
        st.metric("Total Documents", total_docs)
    with col3:
        st.metric("Total Storage", format_bytes(total_size))

    st.divider()

    # Store cards
    for store in stores:
        with st.expander(
            f"📦 **{store['display_name']}** - {store['total_documents']} documents, {format_bytes(store['size_bytes'])}",
            expanded=False,
        ):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**Store Name:** `{store['name']}`")
                st.markdown(f"**Created:** {format_timestamp(store['create_time'])}")

                # Document stats
                st.markdown("**Document Status:**")
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Active", store["active_documents"])
                with col_b:
                    st.metric("Pending", store["pending_documents"])
                with col_c:
                    st.metric("Failed", store["failed_documents"])

                st.metric("Storage", format_bytes(store["size_bytes"]))

            with col2:
                # Action buttons
                if st.button("📂 View Files", key=f"view_{store['name']}", type="primary"):
                    st.session_state.selected_store = store["name"]
                    st.session_state.view_store_files = True
                    st.rerun()

                if st.button("🗑️ Delete Store", key=f"del_store_{store['name']}", type="secondary"):
                    st.session_state.confirm_delete_store = store["name"]
                    st.rerun()

            # Confirm delete dialog
            if st.session_state.get("confirm_delete_store") == store["name"]:
                st.warning(
                    f"⚠️ Are you sure you want to delete **{store['display_name']}**? "
                    f"This will permanently delete all {store['total_documents']} documents."
                )
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Yes, Delete", key=f"confirm_yes_{store['name']}", type="primary"):
                        with st.spinner("Deleting store..."):
                            if delete_store(client, store["name"], force=True):
                                st.success(f"Store '{store['display_name']}' deleted!")
                                if "confirm_delete_store" in st.session_state:
                                    del st.session_state.confirm_delete_store
                                if st.session_state.get("store_name") == store["name"]:
                                    del st.session_state.store_name
                                time.sleep(1)
                                st.rerun()
                with col2:
                    if st.button("❌ Cancel", key=f"confirm_no_{store['name']}"):
                        del st.session_state.confirm_delete_store
                        st.rerun()


def render_store_files_view(client: genai.Client, store_name: str):
    """Render detailed file view for a specific store."""
    st.header("📂 Store Files")

    # Get store info
    stats = get_store_stats(client, store_name)
    if stats:
        st.subheader(f"📦 {stats['display_name']}")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total", stats["total_documents"])
        with col2:
            st.metric("Active", stats["active_documents"])
        with col3:
            st.metric("Pending", stats["pending_documents"])
        with col4:
            st.metric("Storage", format_bytes(stats["size_bytes"]))

    st.divider()

    # Back button
    if st.button("⬅️ Back to All Stores"):
        if "view_store_files" in st.session_state:
            del st.session_state.view_store_files
        if "selected_store" in st.session_state:
            del st.session_state.selected_store
        st.rerun()

    # List documents
    documents = list_all_documents(client, store_name)

    if not documents:
        st.info("No documents in this store")
        return

    # Filter options
    col1, col2, col3 = st.columns(3)

    with col1:
        state_filter = st.selectbox(
            "Filter by State",
            ["All", "STATE_ACTIVE", "STATE_PENDING", "STATE_FAILED"],
            key="state_filter_view",
        )

    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Upload Time (Newest)", "Upload Time (Oldest)", "Name", "Size"],
            key="sort_by_view",
        )

    with col3:
        search_term = st.text_input("Search", placeholder="Search by name...", key="search_view")

    # Apply filters
    filtered_docs = documents

    if state_filter != "All":
        filtered_docs = [d for d in filtered_docs if d["state"] == state_filter]

    if search_term:
        filtered_docs = [
            d for d in filtered_docs
            if search_term.lower() in d["display_name"].lower()
        ]

    # Apply sorting
    if sort_by == "Upload Time (Newest)":
        filtered_docs.sort(key=lambda x: x["create_time"], reverse=True)
    elif sort_by == "Upload Time (Oldest)":
        filtered_docs.sort(key=lambda x: x["create_time"])
    elif sort_by == "Name":
        filtered_docs.sort(key=lambda x: x["display_name"])
    elif sort_by == "Size":
        filtered_docs.sort(key=lambda x: x["size_bytes"], reverse=True)

    st.caption(f"Showing {len(filtered_docs)} of {len(documents)} documents")

    # Document table
    for doc in filtered_docs:
        with st.expander(
            f"📄 {doc['display_name']} - {format_bytes(doc['size_bytes'])}"
        ):
            col1, col2 = st.columns([3, 1])

            with col1:
                # Basic info
                st.markdown(f"**Status:** `{doc['state']}`")
                st.markdown(f"**Type:** {doc['mime_type']}")
                st.markdown(f"**Size:** {format_bytes(doc['size_bytes'])}")
                st.markdown(f"**Uploaded:** {format_timestamp(doc['create_time'])}")
                st.markdown(f"**Updated:** {format_timestamp(doc['update_time'])}")

                # Custom metadata
                if doc["custom_metadata"]:
                    st.markdown("**Custom Metadata:**")
                    for key, value in doc["custom_metadata"].items():
                        st.markdown(f"- `{key}`: {value}")

                # Document ID (show/hide toggle)
                show_id_key = f"show_id_{doc['id']}"
                if st.session_state.get(show_id_key, False):
                    st.markdown("**Document ID:**")
                    st.code(doc["id"], language=None)
                    if st.button("Hide ID", key=f"hide_id_{doc['id']}"):
                        st.session_state[show_id_key] = False
                        st.rerun()
                else:
                    if st.button("🔍 Show Document ID", key=f"show_id_btn_{doc['id']}"):
                        st.session_state[show_id_key] = True
                        st.rerun()

            with col2:
                # Action buttons
                if st.button("🗑️ Delete", key=f"delete_{doc['id']}", type="secondary"):
                    with st.spinner("Deleting..."):
                        if delete_document(client, doc["id"]):
                            st.success("Deleted!")
                            time.sleep(0.5)
                            st.rerun()

                if st.button("📋 Details", key=f"details_{doc['id']}"):
                    st.session_state.selected_doc = doc["id"]
                    st.rerun()

    # Show detailed view if document selected
    if "selected_doc" in st.session_state:
        doc_details = get_document_details(client, st.session_state.selected_doc)
        if doc_details:
            st.divider()
            st.subheader("📋 Document Details")

            col1, col2 = st.columns([3, 1])

            with col1:
                st.json(doc_details)

            with col2:
                if st.button("Close Details"):
                    del st.session_state.selected_doc
                    st.rerun()


def render_document_inventory(client: genai.Client, store_name: str):
    """Render comprehensive document inventory table."""
    st.subheader("📚 Document Inventory")

    documents = list_all_documents(client, store_name)

    if not documents:
        st.info("No documents in store")
        return

    # Filter options
    col1, col2, col3 = st.columns(3)

    with col1:
        state_filter = st.selectbox(
            "Filter by State",
            ["All", "STATE_ACTIVE", "STATE_PENDING", "STATE_FAILED"],
            key="state_filter",
        )

    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Upload Time (Newest)", "Upload Time (Oldest)", "Name", "Size"],
            key="sort_by",
        )

    with col3:
        search_term = st.text_input("Search", placeholder="Search by name...", key="search")

    # Apply filters
    filtered_docs = documents

    if state_filter != "All":
        filtered_docs = [d for d in filtered_docs if d["state"] == state_filter]

    if search_term:
        filtered_docs = [
            d for d in filtered_docs
            if search_term.lower() in d["display_name"].lower()
        ]

    # Apply sorting
    if sort_by == "Upload Time (Newest)":
        filtered_docs.sort(key=lambda x: x["create_time"], reverse=True)
    elif sort_by == "Upload Time (Oldest)":
        filtered_docs.sort(key=lambda x: x["create_time"])
    elif sort_by == "Name":
        filtered_docs.sort(key=lambda x: x["display_name"])
    elif sort_by == "Size":
        filtered_docs.sort(key=lambda x: x["size_bytes"], reverse=True)

    st.caption(f"Showing {len(filtered_docs)} of {len(documents)} documents")

    # Document table
    for doc in filtered_docs:
        with st.expander(
            f"📄 {doc['display_name']} - {format_bytes(doc['size_bytes'])}"
        ):
            col1, col2 = st.columns([3, 1])

            with col1:
                # Basic info
                st.markdown(f"**Status:** `{doc['state']}`")
                st.markdown(f"**Type:** {doc['mime_type']}")
                st.markdown(f"**Size:** {format_bytes(doc['size_bytes'])}")
                st.markdown(f"**Uploaded:** {format_timestamp(doc['create_time'])}")
                st.markdown(f"**Updated:** {format_timestamp(doc['update_time'])}")

                # Custom metadata
                if doc["custom_metadata"]:
                    st.markdown("**Custom Metadata:**")
                    for key, value in doc["custom_metadata"].items():
                        st.markdown(f"- `{key}`: {value}")

                # Document ID (show/hide toggle)
                show_id_key = f"show_id_{doc['id']}"
                if st.session_state.get(show_id_key, False):
                    st.markdown("**Document ID:**")
                    st.code(doc["id"], language=None)
                    if st.button("Hide ID", key=f"hide_id_{doc['id']}"):
                        st.session_state[show_id_key] = False
                        st.rerun()
                else:
                    if st.button("🔍 Show Document ID", key=f"show_id_btn_{doc['id']}"):
                        st.session_state[show_id_key] = True
                        st.rerun()

            with col2:
                # Action buttons
                if st.button("🗑️ Delete", key=f"delete_{doc['id']}", type="secondary"):
                    if delete_document(client, doc["id"]):
                        st.success("Deleted!")
                        st.rerun()

                if st.button("📋 Details", key=f"details_{doc['id']}"):
                    st.session_state.selected_doc = doc["id"]

    # Show detailed view if document selected
    if "selected_doc" in st.session_state:
        doc_details = get_document_details(client, st.session_state.selected_doc)
        if doc_details:
            st.divider()
            st.subheader("📋 Document Details")

            col1, col2 = st.columns([3, 1])

            with col1:
                st.json(doc_details)

            with col2:
                if st.button("Close Details"):
                    del st.session_state.selected_doc
                    st.rerun()


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="RAG with Gemini - File Inventory",
        page_icon="🤖",
        layout="wide",
    )

    st.title("🤖 RAG with Gemini - Complete File Inventory")
    st.caption("Comprehensive document management with Google Gemini File Search")

    # Initialize client
    client = init_genai()

    # Check if viewing specific store files
    if st.session_state.get("view_store_files") and st.session_state.get("selected_store"):
        render_store_files_view(client, st.session_state.selected_store)
        return

    # Sidebar - Store Management & Upload
    with st.sidebar:
        st.header("🏪 Quick Store Selector")

        # Store selector
        stores = list_all_stores(client)

        if stores:
            store_options = {
                f"{s['display_name']} ({s['total_documents']} docs)": s["name"]
                for s in stores
            }

            # Add default selection
            default_store = st.session_state.get("store_name")
            default_index = 0
            if default_store:
                for i, (_, name) in enumerate(store_options.items()):
                    if name == default_store:
                        default_index = i
                        break

            selected_store_display = st.selectbox(
                "Active Store",
                list(store_options.keys()),
                index=default_index,
                key="store_selector",
            )
            store_name = store_options[selected_store_display]

            # Update session state
            st.session_state.store_name = store_name

            # Show current store info
            current_stats = get_store_stats(client, store_name)
            if current_stats:
                st.info(
                    f"**{current_stats['total_documents']}** docs | "
                    f"**{format_bytes(current_stats['size_bytes'])}**"
                )
        else:
            store_name = get_or_create_file_search_store(client)
            st.info("Default store created")

        st.divider()

        # Create new store
        with st.expander("➕ Create New Store"):
            new_store_name = st.text_input("Store Display Name", key="new_store")
            if st.button("Create Store", type="primary", key="create_store_btn"):
                if new_store_name:
                    with st.spinner("Creating store..."):
                        new_store_id = create_store(client, new_store_name)
                        if new_store_id:
                            st.success(f"Created store: {new_store_name}")
                            st.session_state.store_name = new_store_id
                            time.sleep(1)
                            st.rerun()
                else:
                    st.warning("Please enter a store name")

        st.divider()

        # Upload section
        st.header("📤 Upload Document")

        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["txt", "pdf", "doc", "docx", "csv", "xlsx", "pptx", "md", "html"],
            help="Upload documents to the active store",
        )

        if uploaded_file:
            # Default to filename without extension
            default_name = os.path.splitext(uploaded_file.name)[0]

            # Display name input (prominent)
            custom_display_name = st.text_input(
                "Document Name *",
                value=default_name,
                placeholder="Enter a descriptive name",
                key="custom_name",
                help="Give your document a clear, searchable name",
            )

            # Advanced upload options
            with st.expander("⚙️ Advanced Options"):
                st.markdown("**Custom Metadata (optional)**")
                col1, col2 = st.columns(2)
                with col1:
                    meta_key1 = st.text_input("Key 1", key="meta_key1")
                with col2:
                    meta_val1 = st.text_input("Value 1", key="meta_val1")

                col1, col2 = st.columns(2)
                with col1:
                    meta_key2 = st.text_input("Key 2", key="meta_key2")
                with col2:
                    meta_val2 = st.text_input("Value 2", key="meta_val2")

                st.markdown("**Chunking Configuration**")
                chunk_size = st.slider(
                    "Chunk Size (tokens)", 100, 2000, 400, 50, key="chunk_size"
                )
                chunk_overlap = st.slider(
                    "Chunk Overlap (tokens)", 0, 200, 40, 10, key="chunk_overlap"
                )

            # Build metadata dict
            metadata = {}
            if meta_key1 and meta_val1:
                metadata[meta_key1] = meta_val1
            if meta_key2 and meta_val2:
                metadata[meta_key2] = meta_val2

            if st.button("📤 Upload to Active Store", type="primary", use_container_width=True):
                if not custom_display_name:
                    st.error("Please enter a document name")
                else:
                    with st.spinner("Uploading document..."):
                        success = upload_document(
                            client,
                            store_name,
                            uploaded_file,
                            display_name=custom_display_name,
                            metadata=metadata if metadata else None,
                            chunk_size=chunk_size,
                            chunk_overlap=chunk_overlap,
                        )
                        if success:
                            st.success(f"✅ '{custom_display_name}' uploaded!")
                            time.sleep(1)
                            st.rerun()

    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["🏪 All Stores", "💬 Chat", "📊 Analytics", "📚 Inventory", "ℹ️ About"]
    )

    with tab1:
        # All stores overview
        render_all_stores_overview(client)

        # Create store section
        st.divider()
        st.subheader("➕ Create New Store")
        col1, col2 = st.columns([3, 1])
        with col1:
            new_store_display = st.text_input(
                "Store Display Name",
                placeholder="e.g., Research Papers, Legal Documents, etc.",
                key="new_store_main",
            )
        with col2:
            st.write("")  # Spacer
            st.write("")  # Spacer
            if st.button("Create", type="primary", key="create_main"):
                if new_store_display:
                    with st.spinner("Creating store..."):
                        new_id = create_store(client, new_store_display)
                        if new_id:
                            st.success(f"✅ Created '{new_store_display}'")
                            st.session_state.store_name = new_id
                            time.sleep(1)
                            st.rerun()
                else:
                    st.warning("Please enter a store name")

    with tab2:
        # Chat interface
        col1, col2 = st.columns([3, 1])
        with col2:
            use_google_search = st.checkbox(
                "Use Google Search",
                help="Use Google Search instead of uploaded documents",
            )

        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message.get("citations"):
                    with st.expander("📖 Citations"):
                        for citation in message["citations"]:
                            st.text(f"• {citation}")

        # Chat input
        if prompt := st.chat_input("Ask a question about your documents..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Get assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response_text, citations = chat_with_documents(
                        client, store_name, prompt, use_google_search
                    )

                if response_text:
                    st.markdown(response_text)

                    if citations:
                        with st.expander("📖 Citations"):
                            for citation in citations:
                                st.text(f"• {citation}")

                    # Add to chat history
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": response_text,
                            "citations": citations,
                        }
                    )

        # Clear chat button
        if st.session_state.messages and st.button("Clear Chat"):
            st.session_state.messages = []
            st.rerun()

    with tab3:
        # Analytics dashboard
        stats = get_store_stats(client, store_name)
        if stats:
            render_store_analytics(stats)

    with tab4:
        # Document inventory
        render_document_inventory(client, store_name)

    with tab5:
        st.markdown("""
        ## About This Application

        This is a comprehensive RAG (Retrieval-Augmented Generation) application with complete
        file inventory management using:
        - **Google Gemini 2.5 Flash** for chat
        - **Gemini File Search API** for document retrieval
        - **Streamlit** for the user interface

        ### Features

        **🏪 Complete Store Management**
        - View all stores in your account
        - Create new stores for different document collections
        - Delete stores (with confirmation)
        - Switch between stores seamlessly
        - View files in each store
        - Monitor storage and document counts per store

        **📚 Complete File Inventory Management**
        - View all documents with full metadata
        - Track document status (Active, Pending, Failed)
        - Custom metadata support
        - Advanced filtering and sorting
        - Detailed document information

        **📊 Store Analytics**
        - Real-time storage usage tracking
        - Document status breakdown
        - Store creation and management

        **📤 Advanced Upload Options**
        - Prominent document naming
        - Custom display names for organization
        - Custom metadata (key-value pairs)
        - Configurable chunking (size and overlap)
        - Progress tracking

        **💬 Smart Chat**
        - Chat with your documents using AI
        - View citations and sources
        - Optional Google Search mode
        - Chat history management

        ### File Lifecycle

        1. **Upload** - Documents are uploaded and processed
        2. **Processing** - Documents are chunked and embedded (STATE_PENDING)
        3. **Active** - Documents are ready for search (STATE_ACTIVE)
        4. **Query** - Documents are searched during chat
        5. **Manage** - View, update metadata, or delete documents
        6. **Delete** - Remove documents and free storage

        ### Supported File Types

        Text, PDF, DOC, DOCX, CSV, XLSX, PPTX, Markdown, HTML, and various code files
        (Python, JavaScript, Java, Go, Rust, TypeScript, etc.)

        ### Limits

        - Maximum file size: 100 MB
        - Recommended store size: < 20 GB
        - Maximum stores per project: 10
        - Maximum metadata entries: 20 per document
        - Maximum chunk size: 2043 tokens
        """)


if __name__ == "__main__":
    main()
