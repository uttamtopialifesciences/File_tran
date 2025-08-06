import streamlit as st
import random
import os
import tempfile
import shutil
from datetime import datetime, timedelta
import json

# Configure page
st.set_page_config(
    page_title="Secure File Transfer",
    page_icon="📁",
    layout="wide"
)

# Initialize session state for storing file data
if 'file_storage' not in st.session_state:
    st.session_state.file_storage = {}

def generate_pin():
    """Generate a random 4-digit PIN"""
    return f"{random.randint(1000, 9999)}"

def save_file_with_pin(uploaded_file, pin):
    """Save uploaded file with PIN as identifier"""
    # Create temporary directory if it doesn't exist
    temp_dir = tempfile.gettempdir()
    app_dir = os.path.join(temp_dir, "streamlit_file_transfer")
    os.makedirs(app_dir, exist_ok=True)
    
    # Save file with PIN as filename prefix
    file_path = os.path.join(app_dir, f"{pin}_{uploaded_file.name}")
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getvalue())
    
    # Store file info in session state
    st.session_state.file_storage[pin] = {
        'filename': uploaded_file.name,
        'filepath': file_path,
        'size': uploaded_file.size,
        'upload_time': datetime.now(),
        'type': uploaded_file.type
    }
    
    return file_path

def get_file_by_pin(pin):
    """Retrieve file information by PIN"""
    return st.session_state.file_storage.get(pin)

def cleanup_old_files():
    """Clean up files older than 24 hours"""
    current_time = datetime.now()
    pins_to_remove = []
    
    for pin, file_info in st.session_state.file_storage.items():
        if current_time - file_info['upload_time'] > timedelta(hours=24):
            # Remove file from disk
            if os.path.exists(file_info['filepath']):
                os.remove(file_info['filepath'])
            pins_to_remove.append(pin)
    
    # Remove from session state
    for pin in pins_to_remove:
        del st.session_state.file_storage[pin]

# Clean up old files on app start
cleanup_old_files()

# App title and description
st.title("🔒 Secure File Transfer")
st.markdown("Upload files and share them securely with a 4-digit PIN")

# Create tabs for upload and download
tab1, tab2, tab3 = st.tabs(["📤 Upload File", "📥 Download File", "ℹ️ How it Works"])

with tab1:
    st.header("Upload Your File")
    st.markdown("Upload a file to generate a secure PIN for sharing")
    
    uploaded_file = st.file_uploader(
        "Choose a file to upload",
        type=None,  # Allow all file types
        help="Select any file to upload and generate a PIN"
    )
    
    if uploaded_file is not None:
        # Display file info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("File Name", uploaded_file.name)
        with col2:
            st.metric("File Size", f"{uploaded_file.size / 1024:.1f} KB")
        with col3:
            st.metric("File Type", uploaded_file.type or "Unknown")
        
        # Generate PIN button
        if st.button("🔐 Generate PIN & Upload", type="primary", use_container_width=True):
            pin = generate_pin()
            
            try:
                file_path = save_file_with_pin(uploaded_file, pin)
                
                # Success message with PIN
                st.success("File uploaded successfully!")
                
                # Display PIN prominently
                st.markdown("---")
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.markdown(
                        f"""
                        <div style='
                            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
                            padding: 20px;
                            border-radius: 10px;
                            text-align: center;
                            margin: 20px 0;
                        '>
                            <h2 style='color: white; margin: 0;'>Your PIN</h2>
                            <h1 style='color: white; font-size: 3em; margin: 10px 0; letter-spacing: 0.2em;'>{pin}</h1>
                            <p style='color: white; margin: 0;'>Share this PIN to allow file download</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                st.info("⏰ **Important:** This PIN will expire in 24 hours for security reasons.")
                st.warning("🔒 **Security Note:** Only share this PIN with trusted recipients.")
                
            except Exception as e:
                st.error(f"Error uploading file: {str(e)}")

with tab2:
    st.header("Download File")
    st.markdown("Enter the 4-digit PIN to download the shared file")
    
    # PIN input
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        pin_input = st.text_input(
            "Enter 4-digit PIN",
            max_chars=4,
            placeholder="1234",
            help="Enter the PIN provided by the file sender"
        )
    
    if pin_input:
        if len(pin_input) == 4 and pin_input.isdigit():
            file_info = get_file_by_pin(pin_input)
            
            if file_info:
                # Display file information
                st.success("✅ PIN verified! File found.")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("File Name", file_info['filename'])
                with col2:
                    st.metric("File Size", f"{file_info['size'] / 1024:.1f} KB")
                with col3:
                    st.metric("File Type", file_info['type'] or "Unknown")
                with col4:
                    time_remaining = 24 - int((datetime.now() - file_info['upload_time']).total_seconds() / 3600)
                    st.metric("Expires in", f"{max(0, time_remaining)} hours")
                
                # Download button
                try:
                    with open(file_info['filepath'], 'rb') as file:
                        file_data = file.read()
                    
                    st.download_button(
                        label="📥 Download File",
                        data=file_data,
                        file_name=file_info['filename'],
                        mime=file_info['type'],
                        type="primary",
                        use_container_width=True
                    )
                    
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
                    st.info("The file might have been moved or deleted.")
            else:
                st.error("❌ Invalid PIN or file has expired.")
                st.info("Please check the PIN or contact the file sender.")
        else:
            if pin_input:  # Only show error if user has entered something
                st.warning("Please enter a valid 4-digit PIN")

with tab3:
    st.header("How It Works")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚀 For Senders")
        st.markdown("""
        1. **Upload**: Select and upload your file
        2. **Generate**: Click to generate a secure 4-digit PIN
        3. **Share**: Send the PIN to your recipient
        4. **Secure**: File expires automatically in 24 hours
        """)
        
        st.subheader("🔒 Security Features")
        st.markdown("""
        - Random 4-digit PIN generation
        - 24-hour automatic expiration
        - Secure temporary file storage
        - No permanent file retention
        """)
    
    with col2:
        st.subheader("📱 For Recipients")
        st.markdown("""
        1. **Receive**: Get the 4-digit PIN from sender
        2. **Enter**: Input PIN in the Download tab
        3. **Verify**: System verifies PIN and shows file info
        4. **Download**: Click to download the file
        """)
        
        st.subheader("⚠️ Important Notes")
        st.markdown("""
        - Files expire after 24 hours
        - PINs are case-sensitive numbers only
        - Keep PINs confidential and secure
        - Files are temporarily stored and automatically cleaned up
        """)

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col2:
    st.markdown(
        "<p style='text-align: center; color: gray;'>🔐 Secure File Transfer App</p>",
        unsafe_allow_html=True
    )

# Display active transfers (for debugging/admin purposes)
if st.session_state.file_storage:
    with st.expander("📊 Active Transfers (Admin View)", expanded=False):
        for pin, info in st.session_state.file_storage.items():
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.text(f"PIN: {pin}")
            with col2:
                st.text(f"File: {info['filename']}")
            with col3:
                st.text(f"Size: {info['size']/1024:.1f} KB")
            with col4:
                hours_left = 24 - int((datetime.now() - info['upload_time']).total_seconds() / 3600)
                st.text(f"Expires: {max(0, hours_left)}h")
