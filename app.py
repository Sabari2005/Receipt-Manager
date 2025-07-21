import streamlit as st
from datetime import date, timedelta
import pandas as pd
import json
from io import StringIO
import io
from typing import Optional
import time
import plotly.express as px
from models import CategoryEnum
from service_layer import ReceiptProcessor
import streamlit.components.v1 as components

st.set_page_config(page_title="Receipt Manager", layout="wide", page_icon="🧾")

st.markdown("""
    <style>
    /* Main header styles with gradient animation */
    .custom-header {
        background-color: #121212;
        padding: 40px 30px 30px 30px;
        border-radius: 16px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
        position: relative;
        overflow: hidden;
        margin-bottom: 2rem;
        background: linear-gradient(135deg, #121212, #1a1a2e);
        animation: gradientBG 15s ease infinite;
        background-size: 400% 400%;
    }

    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .custom-header::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        height: 6px;
        width: 100%;
        background: linear-gradient(90deg, #ff4b4b, #ff7f50, #ffc107);
        z-index: 1;
        animation: rainbow 8s linear infinite;
    }

    @keyframes rainbow {
        0% { background-position: 0% 50%; }
        100% { background-position: 100% 50%; }
    }

    .header-title {
        font-size: 42px;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 8px;
        letter-spacing: 0.8px;
        z-index: 2;
        position: relative;
        animation: fadeInDown 1s ease;
    }

    .header-subtitle {
        font-size: 18px;
        font-weight: 400;
        color: #b0b0b0;
        margin-top: 4px;
        z-index: 2;
        position: relative;
        animation: fadeInUp 1s ease 0.2s forwards;
        opacity: 0;
    }

    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* Enhanced tooltip with smooth transitions */
    .desc-tooltip {
        position: relative;
        display: inline-block;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .desc-tooltip:hover {
        transform: translateY(-2px);
    }
    
    .desc-tooltip .desc-tooltiptext {
        visibility: hidden;
        width: 400px;
        background-color: #222;
        color: #fff;
        text-align: left;
        border-radius: 8px;
        padding: 16px;
        position: absolute;
        z-index: 100;
        bottom: 125%;
        left: 50%;
        margin-left: -200px;
        opacity: 0;
        transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        box-shadow: 0 8px 24px rgba(0,0,0,0.25);
        white-space: pre-wrap;
        font-size: 14px;
        max-height: 300px;
        overflow-y: auto;
        transform: translateY(10px);
    }
    
    .desc-tooltip:hover .desc-tooltiptext {
        visibility: visible;
        opacity: 1;
        transform: translateY(0);
    }

    /* Floating animation for visual interest */
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }

    .floating-icon {
        animation: float 3s ease-in-out infinite;
        display: inline-block;
        margin-right: 8px;
    }

    /* Pulse animation for important elements */
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }

    .pulse:hover {
        animation: pulse 2s infinite;
    }

    /* Pure CSS particle animation */
    .particles-container {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        overflow: hidden;
        z-index: 0;
        pointer-events: none;
    }
    
    .particle {
        position: absolute;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 50%;
        animation: floatParticle 15s infinite linear;
    }
    
    @keyframes floatParticle {
        0% {
            transform: translateY(100vh) translateX(0);
            opacity: 0;
        }
        10% {
            opacity: 1;
        }
        90% {
            opacity: 1;
        }
        100% {
            transform: translateY(-20vh) translateX(100px);
            opacity: 0;
        }
    }
    
    /* Create multiple particles with different delays and durations */
    .particle:nth-child(1) {
        width: 3px;
        height: 3px;
        left: 10%;
        animation-delay: 0s;
        animation-duration: 15s;
    }
    .particle:nth-child(2) {
        width: 2px;
        height: 2px;
        left: 25%;
        animation-delay: 2s;
        animation-duration: 18s;
    }
    .particle:nth-child(3) {
        width: 4px;
        height: 4px;
        left: 40%;
        animation-delay: 4s;
        animation-duration: 12s;
    }
    .particle:nth-child(4) {
        width: 3px;
        height: 3px;
        left: 55%;
        animation-delay: 1s;
        animation-duration: 20s;
    }
    .particle:nth-child(5) {
        width: 2px;
        height: 2px;
        left: 70%;
        animation-delay: 3s;
        animation-duration: 16s;
    }
    .particle:nth-child(6) {
        width: 3px;
        height: 3px;
        left: 85%;
        animation-delay: 5s;
        animation-duration: 14s;
    }
    
    /* Smooth transitions for all interactive elements */
    .stButton>button, .stTextInput>div>div>input, 
    .stSelectbox>div>div>select, .stDateInput>div>div>input {
        transition: all 0.3s ease !important;
    }

    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="custom-header" style="position: relative;">
        <div class="particles-container">
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
        </div>
        <div class="header-title">
            <span class="floating-icon">🧾</span>Receipt Management System
        </div>
        <div class="header-subtitle">
            Intelligent tracking, analytics, and organization of your receipts
            <div style="margin-top: 12px; font-size: 14px; color: #666;">
                <span class="pulse" style="display: inline-block;">✨</span> 
                Now with enhanced AI-powered insights
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

def get_processor():
    return ReceiptProcessor()

processor = get_processor()

with st.sidebar:
    st.markdown("""
    <style>
        @keyframes slideInFromLeft {
            0% { transform: translateX(-100%); opacity: 0; }
            100% { transform: translateX(0); opacity: 1; }
        }
        .sidebar-header {
            animation: slideInFromLeft 0.5s ease-out;
            border-left: 5px solid #667eea;
            padding-left: 1rem;
        }
    </style>
    <div class="sidebar-header">
    """, unsafe_allow_html=True)

    st.subheader("📄 Upload Receipts")
    uploaded_file = st.file_uploader(
        "Drag & drop or click to browse",
        type=["jpg", "jpeg", "png", "pdf", "txt"],
        label_visibility="collapsed",
        key="file_uploader"
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if uploaded_file:
        def is_valid_file(uploaded_file):
            if not uploaded_file:
                return False
            ext = uploaded_file.name.split(".")[-1].lower()
            if ext not in ["jpg", "jpeg", "png", "pdf", "txt"]:
                st.error("❌ Unsupported file type")
                return False
            if uploaded_file.size > 10 * 1024 * 1024:
                st.error("📏 File too large (max 10MB)")
                return False
            st.success(f"✅ {uploaded_file.name} ready for processing!")
            return True

        if is_valid_file(uploaded_file):
            file_ext = uploaded_file.name.split(".")[-1]
            file_key = f"{uploaded_file.name}_{uploaded_file.size}"

            if st.session_state.get("last_file_key") != file_key:
                with st.spinner("🔍 Processing receipt..."):
                    try:
                        extracted_data = processor.process_uploaded_file(
                            uploaded_file.getvalue(),
                            f".{file_ext}"
                        )
                        st.session_state["last_file_key"] = file_key
                        st.session_state["last_extracted_data"] = extracted_data
                    except Exception as e:
                        st.error(f"❌ Error processing file: {str(e)}")
                        st.session_state["last_extracted_data"] = None
            else:
                extracted_data = st.session_state.get("last_extracted_data")

            if extracted_data:
                with st.expander("✨ Extracted Data", expanded=True):
                    st.markdown("""
                    <style>
                        @keyframes fieldAppear {
                            0% { opacity: 0; transform: scale(0.95); }
                            100% { opacity: 1; transform: scale(1); }
                        }
                        .animated-field {
                            animation: fieldAppear 0.4s ease-out;
                        }
                    </style>
                    """, unsafe_allow_html=True)

                    vendor_name = st.text_input(
                        "🏢 Vendor",
                        value=extracted_data["vendor"]["name"],
                        key="vendor_input"
                    )
                    
                    trans_date = st.date_input(
                        "📅 Date",
                        value=extracted_data["bill"]["transaction_date"],
                        key="date_input"
                    )
                    
                    amount = st.number_input(
                        "💰 Amount",
                        value=extracted_data["bill"]["amount"],
                        min_value=0.01,
                        step=0.01,
                        key="amount_input"
                    )
                    
                    current_cat = extracted_data["vendor"]["category"]
                    if isinstance(current_cat, CategoryEnum):
                        current_cat = current_cat.value
                    
                    category = st.selectbox(
                        "🏷️ Category",
                        options=[c.value for c in CategoryEnum],
                        index=[c.value for c in CategoryEnum].index(current_cat) if current_cat else 0,
                        key="category_select"
                    )

                    if st.button(
                        "💾 Save Entry", 
                        key="save_entry_btn",
                        use_container_width=True,
                        type="primary"
                    ):
                        extracted_data["vendor"]["name"] = vendor_name
                        extracted_data["bill"]["transaction_date"] = trans_date
                        extracted_data["bill"]["amount"] = amount
                        extracted_data["vendor"]["category"] = category
                        
                        success, message = processor.save_extracted_data(
                            extracted_data,
                            uploaded_file.name
                        )
                        
                        if success:
                            st.balloons()
                            st.success(message)
                            st.session_state["selected_category"] = "All"
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)
    with st.container():
        st.markdown("""
        <style>
            .filter-section {
                transition: all 0.5s ease;
                padding: 1.5rem;
                background: white;
                border-radius: 10px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                margin-top: 1rem;
            }
        </style>
        <div class="filter-section">
        """, unsafe_allow_html=True)
        
        st.subheader("🔍 Filters")
        search_query = st.text_input(
            "Search vendors or descriptions",
            key="search_query",
            placeholder="Type to search...",
            label_visibility="collapsed"
        )

        st.markdown("**Date Range**")
        date_col1, date_col2 = st.columns(2)
        with date_col1:
            start_date = st.date_input(
                "From",
                value=date.today() - timedelta(days=365),
                key="start_date",
                label_visibility="collapsed"
            )
        with date_col2:
            end_date = st.date_input(
                "To",
                value=date.today(),
                key="end_date",
                label_visibility="collapsed"
            )
        categories = ["All"] + [c.value for c in CategoryEnum]
        selected_category = st.selectbox(
            "Category Filter",
            options=categories,
            key="selected_category",
            index=categories.index(st.session_state.get("selected_category", "All"))
        )

        st.markdown("**Amount Range**")
        amount_range = st.slider(
            "Select amount range",
            min_value=0.0,
            max_value=100000.0,
            value=(0.0, 5000.0),
            key="amount_range",
            label_visibility="collapsed"
        )
    st.markdown("""
    <style>
        /* Smooth transitions for all sidebar elements */
        .sidebar .element-container {
            transition: all 0.3s ease;
        }
        
        /* Button hover effects */
        .sidebar .stButton>button {
            transition: all 0.2s ease;
        }
        .sidebar .stButton>button:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        /* Input field focus effects */
        .sidebar .stTextInput>div>div>input:focus,
        .sidebar .stSelectbox>div>div>select:focus {
            border-color: #667eea !important;
            box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2) !important;
        }
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
    <style>
    /* Base tab styling with smooth transitions */
    .stTabs [data-baseweb="tab"] {
        font-size: 16px;
        font-weight: 600;
        padding: 12px 30px;
        margin: 0 8px;
        border-bottom: 2px solid transparent;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        color: #aaa;
        position: relative;
        overflow: hidden;
        background: transparent !important;
    }

    /* Active tab styling with animated underline */
    .stTabs [aria-selected="true"] {
        color: #667eea !important;
        background-color: transparent !important;
        transform: translateY(0px);
    }

    /* Animated underline for active tab */
    .stTabs [aria-selected="true"]::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: #667eea;
        animation: underlineGrow 0.3s ease-out forwards;
        border-radius: 3px 3px 0 0;
    }

    @keyframes underlineGrow {
        from { transform: scaleX(0); opacity: 0; }
        to { transform: scaleX(1); opacity: 1; }
    }

    /* Hover effect with subtle lift and color change */
    .stTabs [data-baseweb="tab"]:hover {
        color: #fff !important;
        transform: translateY(-2px);
        background-color: rgba(102, 126, 234, 0.08) !important;
        cursor: pointer;
    }

    /* Pulse animation when switching tabs */
    @keyframes tabPulse {
        0% { transform: translateY(0); }
        50% { transform: translateY(-3px); }
        100% { transform: translateY(0); }
    }

    .stTabs [aria-selected="true"] {
        animation: tabPulse 0.4s ease;
    }

    /* Tab container styling */
    .stTabs [role="tablist"] {
        border-bottom: 1px solid rgba(102, 126, 234, 0.2);
        padding-bottom: 2px;
        margin-bottom: 1rem;
    }

    /* Tab content area transition */
    .stTabs [role="tabpanel"] {
        animation: fadeIn 0.3s ease-out;
    }

    @keyframes fadeIn {
        from { opacity: 0.8; transform: translateY(5px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs([
    "   Entries   ",
    "   Analytics   ",
    "   Export   "
])

st.markdown("""
    <style>
    .tab-indicator {
        display: flex;
        justify-content: center;
        gap: 60px;
        margin-bottom: -10px;
        position: relative;
        z-index: 1;
    }
    .tab-emoji {
        font-size: 24px;
        opacity: 0.3;
        transition: all 0.3s ease;
    }
    .tab-emoji.active {
        opacity: 1;
        transform: translateY(-5px);
        filter: drop-shadow(0 2px 4px rgba(255, 75, 75, 0.3));
    }
    </style>
    <div class="tab-indicator">
        <span id="tab1-emoji" class="tab-emoji">📋</span>
        <span id="tab2-emoji" class="tab-emoji">📊</span>
        <span id="tab3-emoji" class="tab-emoji">💾</span>
    </div>
    <script>
    // This simple script will be ignored by Streamlit but won't cause errors
    document.querySelectorAll('[role="tab"]').forEach((tab, index) => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab-emoji').forEach(emoji => {
                emoji.classList.remove('active');
            });
            document.getElementById(`tab${index+1}-emoji`).classList.add('active');
        });
    });
    // Activate first tab by default
    document.getElementById('tab1-emoji').classList.add('active');
    </script>
""", unsafe_allow_html=True)

with tab1:
    st.markdown("""
    <style>
        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-5px); }
            100% { transform: translateY(0px); }
        }
        .bills-header {
            animation: float 3s ease-in-out infinite;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }
    </style>
    <div class="bills-header">
        <h1 style="color:white;margin:0;">🧾 Bill Management</h1>
    </div>
    """, unsafe_allow_html=True)

    if 'delete_id' in st.session_state:
        delete_id = st.session_state.delete_id
        try:
            with st.container():
                st.warning("Are you sure you want to delete this bill?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Confirm Delete", type="primary"):
                        processor.db_handler.delete_bill(int(delete_id))
                        st.success("Bill deleted successfully!")
                        del st.session_state.delete_id
                        time.sleep(1)
                        st.rerun()
                with col2:
                    if st.button("❌ Cancel"):
                        del st.session_state.delete_id
                        st.rerun()
        except Exception as e:
            st.error(f"Delete failed: {e}")

    sort_options = {
        "Vendor (A-Z)": ("vendor", False),
        "Vendor (Z-A)": ("vendor", True),
        "Amount (Low-High)": ("amount", False),
        "Amount (High-Low)": ("amount", True),
        "Date (Newest)": ("date", True),
        "Date (Oldest)": ("date", False),
        "Category (A-Z)": ("category", False),
        "Category (Z-A)": ("category", True),
    }
    sort_choice = st.selectbox("Sort by", list(sort_options.keys()), key="sort_choice")
    sort_field, sort_reverse = sort_options[sort_choice]

    with st.spinner("🔍 Loading bills..."):
        bills = processor.search_bills(
            query=search_query if search_query else None,
            start_date=start_date,
            end_date=end_date,
            category=CategoryEnum(selected_category) if selected_category != "All" else None,
            min_amount=amount_range[0],
            max_amount=amount_range[1],
            sort_by=sort_field,
            sort_desc=sort_reverse
        )


    if bills:
        df = pd.DataFrame(bills)
        df['date'] = pd.to_datetime(df['date'], errors="coerce").dt.date
        header_cols = st.columns([2, 2, 2, 2, 3, 1, 1])
        headers = ["Vendor", "Amount", "Date", "Category", "Description", "Edit", "Delete"]
        for i, header in enumerate(headers):
            with header_cols[i]:
                st.markdown(f"""
                <div style="
                    padding: 0.5rem;
                    font-weight: bold;
                    border-bottom: 2px solid #667eea;
                    text-align: {'right' if i >= 5 else 'left'};
                ">{header}</div>
                """, unsafe_allow_html=True)

        for idx, row in df.iterrows():
            cols = st.columns([2, 2, 2, 2, 3, 1, 1])

            with cols[0]:
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="
                        width: 24px;
                        height: 24px;
                        background: #667eea;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-size: 12px;
                    ">{row["vendor"][0].upper()}</div>
                    {row["vendor"]}
                </div>
                """, unsafe_allow_html=True)
            
            with cols[1]:
                amount_color = "#4CAF50" if row["amount"] < 100 else "#FF5722"
                st.markdown(f"""
                <div style="color: {amount_color}; font-weight: bold;">
                    ${row["amount"]:,.2f}
                </div>
                """, unsafe_allow_html=True)
            
            with cols[2]:
                delta = (date.today() - row["date"]).days
                if delta == 0:
                    time_str = "Today"
                elif delta == 1:
                    time_str = "Yesterday"
                elif delta < 7:
                    time_str = f"{delta} days ago"
                else:
                    time_str = row["date"].strftime("%b %d, %Y")
                st.write(f"{time_str}")

            with cols[3]:
                if row["category"]:
                    category_color = {
                        "Food": "#4CAF50",
                        "Transport": "#2196F3",
                        "Utilities": "#9C27B0",
                        "Shopping": "#FF9800",
                        "Health": "#F44336",
                        "Other": "#607D8B"
                    }.get(row["category"], "#607D8B")
                    st.markdown(f"""
                    <span style="
                        background: {category_color};
                        color: white;
                        padding: 2px 8px;
                        border-radius: 12px;
                        font-size: 12px;
                    ">{row["category"]}</span>
                    """, unsafe_allow_html=True)
                else:
                    st.write("")

            with cols[4]:
                desc = row["description"] or ""
                short_desc = (desc[:2] + "...") if len(desc) > 2 else desc
                st.markdown(f"""
                <span class="desc-tooltip">
                <span>{short_desc}</span>
                <span class="desc-tooltiptext">{desc.replace('<','&lt;').replace('>','&gt;')}</span>
            </span>
                """, unsafe_allow_html=True)

            with cols[5]:
                if st.button("✏️", key=f"edit_{row['id']}"):
                    st.session_state["edit_id"] = row["id"]
                    st.rerun()

            with cols[6]:
                if st.button("🗑️", key=f"delete_{row['id']}"):
                    st.session_state.delete_id = row["id"]
                    st.rerun()
            st.markdown("""<hr style="margin: 0.5rem 0; border: 0.5px solid #eee;">""", unsafe_allow_html=True)

        edit_id = st.session_state.get("edit_id")
        if edit_id:
            bill_to_edit = next((b for b in bills if b["id"] == edit_id), None)
            if bill_to_edit:
                with st.expander(f"✏️ Editing Bill #{edit_id}", expanded=True):
                    with st.form("edit_bill_form"):
                        cols = st.columns(2)
                        with cols[0]:
                            vendor = st.text_input("Vendor", value=bill_to_edit["vendor"])
                            amount = st.number_input("Amount", value=bill_to_edit["amount"], min_value=0.01, step=0.01)
                        with cols[1]:
                            date_val = st.date_input("Date", value=bill_to_edit["date"])
                            category = st.selectbox(
                                "Category", 
                                options=[c.value for c in CategoryEnum], 
                                index=[c.value for c in CategoryEnum].index(bill_to_edit["category"]) if bill_to_edit["category"] else 0
                            )
                        
                        description = st.text_area("Description", value=bill_to_edit["description"] or "", height=100)
                        
                        form_cols = st.columns([1, 1, 3])
                        with form_cols[0]:
                            if st.form_submit_button("💾 Save", type="primary"):
                                processor.db_handler.update_bill(
                                    edit_id,
                                    {
                                        "amount": amount,
                                        "transaction_date": date_val,
                                        "description": description
                                    }
                                )
                                st.success("Bill updated successfully!")
                                time.sleep(1)
                                del st.session_state["edit_id"]
                                st.rerun()
                        with form_cols[1]:
                            if st.form_submit_button("❌ Cancel"):
                                del st.session_state["edit_id"]
                                st.rerun()
    else:
        st.markdown("""
        <style>
            @keyframes bounce {
                0%, 20%, 50%, 80%, 100% {transform: translateY(0);}
                40% {transform: translateY(-20px);}
                60% {transform: translateY(-10px);}
            }
            .empty-state {
                text-align: center;
                padding: 3rem;
                animation: bounce 2s infinite;
            }
        </style>
        <div class="empty-state">
            <h3>📭 No bills found</h3>
            <p>Try adjusting your filters or upload new receipts</p>
        </div>
        """, unsafe_allow_html=True)
with tab2:
    st.markdown("""
    <style>
        @keyframes gradientBG {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-5px); }
            100% { transform: translateY(0px); }
        }
        .analytics-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            background-size: 200% 200%;
            animation: gradientBG 15s ease infinite, float 3s ease-in-out infinite;
            padding: 1.5rem;
            border-radius: 10px;
            color: white;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }
    </style>
    <div class="analytics-header">
        <h1 style="color:white;margin:0;">📊 Spending Analytics</h1>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown("### 💰 Summary Statistics")
        stats = processor.get_statistics()
        
        if stats:
            cols = st.columns(5)
            metrics = [
                ("Total Spent", f"${stats['total']:,.2f}", "#4CAF50"),
                ("Average Bill", f"${stats['average']:,.2f}", "#2196F3"),
                ("Median Bill", f"${stats['median']:,.2f}", "#9C27B0"),
                ("Largest Bill", f"${stats['max']:,.2f}", "#FF5722"),
                ("Most Common", f"${stats.get('mode', 0):,.2f}", "#607D8B")
            ]
            
            for i, (label, value, color) in enumerate(metrics):
                with cols[i]:
                    st.markdown(f"""
                    <div style="
                        background: {color};
                        padding: 1rem;
                        border-radius: 10px;
                        color: white;
                        text-align: center;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                        transition: transform 0.3s;
                        animation: fadeIn 0.5s ease-in-out;
                    ">
                        <div style="font-size: 0.9rem;">{label}</div>
                        <div style="font-size: 1.5rem; font-weight: bold;">{value}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No data available for statistics")

    with st.expander("📈 Vendor Analysis", expanded=True):
        bills_df = processor.export_to_dataframe()
        
        if not bills_df.empty:
            tab1, tab2 = st.tabs(["Vendor Frequency", "Top Vendors"])
            
            with tab1:
                vendor_counts = bills_df["Vendor"].value_counts().reset_index()
                vendor_counts.columns = ["Vendor", "Frequency"]
                
                fig = px.bar(
                    vendor_counts.head(20),
                    x="Vendor",
                    y="Frequency",
                    color="Frequency",
                    color_continuous_scale="Viridis",
                    title="Vendor Frequency Distribution"
                )
                fig.update_layout(
                    hovermode="x unified",
                    xaxis_title="Vendor",
                    yaxis_title="Count"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                top_vendors = bills_df.groupby("Vendor")["Amount"].sum().sort_values(ascending=False).head(10)
                st.dataframe(
                    top_vendors.reset_index().rename(columns={"Amount": "Total Spend"}),
                    use_container_width=True,
                    height=400
                )
        else:
            st.info("No vendor data available")

    with st.expander("⏳ Time Series Analysis", expanded=True):
        if not bills_df.empty:
            bills_df["Date"] = pd.to_datetime(bills_df["Date"], errors="coerce")
            
            tab1, tab2 = st.tabs(["Monthly Trends", "Daily Trends"])
            
            with tab1:
                monthly = bills_df.groupby(pd.Grouper(key="Date", freq="ME"))["Amount"].sum().reset_index()
                monthly["Rolling Mean"] = monthly["Amount"].rolling(window=3, min_periods=1).mean()
                
                fig = px.line(
                    monthly,
                    x="Date",
                    y=["Amount", "Rolling Mean"],
                    title="Monthly Spend & 3-Month Rolling Mean",
                    labels={"value": "Spend", "variable": "Legend"}
                )
                fig.update_traces(line=dict(width=3))
                st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                daily = bills_df.groupby("Date")["Amount"].sum().reset_index()
                fig2 = px.bar(
                    daily,
                    x="Date",
                    y="Amount",
                    title="Daily Billing Trend",
                    color="Amount",
                    color_continuous_scale="Bluered"
                )
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No time series data available")

    st.markdown("""
    <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .stDataFrame, .stPlotlyChart, .element-container {
            animation: fadeIn 0.8s ease-out;
        }
        
        .stTabs [role="tab"] {
            transition: all 0.3s ease;
        }
        
        .stTabs [role="tab"]:hover {
            background: rgba(0,0,0,0.05);
        }
        
        .stTabs [aria-selected="true"] {
            font-weight: bold;
            border-bottom: 3px solid #4facfe;
        }
    </style>
    """, unsafe_allow_html=True)

with tab3:
    st.markdown("""
    <style>
        @keyframes gradientBGExport {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        @keyframes floatExport {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-5px); }
            100% { transform: translateY(0px); }
        }
        .export-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            background-size: 200% 200%;
            animation: gradientBGExport 15s ease infinite, floatExport 3s ease-in-out infinite;
            padding: 1.5rem;
            border-radius: 10px;
            color: white;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }
    </style>
    <div class="export-header">
        <h1 style="color:white;margin:0;">📤 Export Data</h1>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("Customize Your Export")
    st.caption("Select date range, category, and format for your export")
    
    with st.expander("🔍 Export Filters", expanded=True):
        cols = st.columns([1,1,2])
        with cols[0]:
            export_start = st.date_input(
                "From Date", 
                value=date.today() - timedelta(days=30),
                key="export_start",
                help="Start date for export range"
            )
        with cols[1]:
            export_end = st.date_input(
                "To Date", 
                value=date.today(),
                key="export_end",
                help="End date for export range"
            )
        
        export_categories = ["All"] + [c.value for c in CategoryEnum]
        export_selected_category = st.selectbox(
            "Category Filter",
            options=export_categories,
            key="export_category",
            help="Filter by specific category"
        )
    st.markdown("### Select Export Format")
    export_format = st.radio(
        "Format",
        options=["CSV", "JSON", "Excel"],
        format_func=lambda x: f"{x} 📄",
        horizontal=True,
        label_visibility="collapsed"
    )
    if st.button(
        "✨ Generate Export", 
        key="export_button",
        use_container_width=True,
        type="primary"
    ):
        with st.spinner("Preparing your data..."):
            try:
                time.sleep(0.5) 
                
                df = processor.export_to_dataframe()
                if not df.empty:
                    start_ts = pd.to_datetime(export_start)
                    end_ts = pd.to_datetime(export_end)
                    df = df[(pd.to_datetime(df["Date"]) >= start_ts) & (pd.to_datetime(df["Date"]) <= end_ts)]
                    
                    if export_selected_category != "All":
                        df = df[df["Category"] == export_selected_category]
                    
                    with st.expander("🛠️ Select Columns", expanded=True):
                        export_columns = st.multiselect(
                            "Choose columns to include:",
                            options=list(df.columns),
                            default=list(df.columns),
                            key="export_columns",
                            label_visibility="collapsed"
                        )
                    
                    if export_columns:
                        df = df[export_columns]
                    
                    st.markdown("### Preview (First 20 Rows)")
                    st.dataframe(
                        df.head(20),
                        use_container_width=True,
                        height=400,
                        hide_index=True
                    )
                    col1, col2 = st.columns([1,3])
                    with col1:
                        st.markdown("### Download Options")
                    
                    with col2:
                        if export_format == "CSV":
                            csv = df.to_csv(index=False)
                            st.download_button(
                                "⬇️ Download CSV",
                                data=csv,
                                file_name=f"receipts_export_{date.today()}.csv",
                                mime="text/csv",
                                help="Download as CSV file",
                                use_container_width=True
                            )
                        elif export_format == "JSON":
                            json_data = df.to_json(orient="records", indent=2)
                            st.download_button(
                                "⬇️ Download JSON",
                                data=json_data,
                                file_name=f"receipts_export_{date.today()}.json",
                                mime="application/json",
                                help="Download as JSON file",
                                use_container_width=True
                            )
                        else:  
                            output = io.BytesIO()
                            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                                df.to_excel(writer, index=False, sheet_name='Receipts')
                            st.download_button(
                                "⬇️ Download Excel",
                                data=output.getvalue(),
                                file_name=f"receipts_export_{date.today()}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                help="Download as Excel file",
                                use_container_width=True
                            )
                    
                    st.balloons()
                else:
                    st.info("ℹ️ No data available to export matching your criteria")
            
            except Exception as e:
                st.error(f"❌ Error generating export: {str(e)}")
                st.exception(e)

st.markdown("""
<style>
    /* Button animations */
    .stButton>button {
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Fade-in animation for data */
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    .stDataFrame {
        animation: fadeIn 0.5s ease-in;
    }
    
    /* Pulse animation for download buttons */
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    .stDownloadButton>button {
        animation: pulse 2s infinite;
    }
</style>
""", unsafe_allow_html=True)