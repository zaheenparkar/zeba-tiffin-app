import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Zeba's Authentic Indian Tiffin Service",
    page_icon="🍱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM BRAND STYLING (Maroon, Gold & Cream Theme) ---
st.markdown("""
    <style>
    .main { background-color: #FAF7F2; }
    .stApp { background-color: #FAF7F2; }
    .brand-header {
        background: linear-gradient(135deg, #5C0601 0%, #3B0300 100%);
        color: #F8E5B9;
        padding: 24px;
        border-radius: 12px;
        text-align: center;
        border: 2px solid #D4AF37;
        margin-bottom: 20px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.15);
    }
    .brand-title {
        font-family: 'Playfair Display', serif;
        font-size: 32px;
        font-weight: bold;
        color: #D4AF37;
        margin: 0;
    }
    .brand-subtitle { font-size: 16px; color: #FAF7F2; margin-top: 6px; }
    .badge-bar { margin-top: 10px; font-size: 14px; color: #E2C974; }
    .card {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #E6DCCD;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    .sub-active {
        background-color: #E8F5E9; color: #2E7D32; padding: 4px 12px;
        border-radius: 20px; font-weight: bold; display: inline-block;
    }
    .sub-inactive {
        background-color: #FFF3E0; color: #E65100; padding: 4px 12px;
        border-radius: 20px; font-weight: bold; display: inline-block;
    }
    .price-tag { font-size: 20px; font-weight: bold; color: #5C0601; }
    </style>
""", unsafe_allow_html=True)

# --- DATABASE HELPER FUNCTIONS ---
DB_FILE = '/workspace/scratch/tiffin_service.db'

def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS system_settings (key TEXT PRIMARY KEY, value TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, phone TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL, address TEXT, is_subscriber INTEGER DEFAULT 0,
        sub_start_date TEXT, sub_end_date TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS menu_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT NOT NULL, name TEXT NOT NULL,
        price REAL NOT NULL, description TEXT, is_available INTEGER DEFAULT 1
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS daily_tiffin (
        id INTEGER PRIMARY KEY AUTOINCREMENT, date_type TEXT DEFAULT 'Today',
        veg_dish TEXT NOT NULL, non_veg_dish TEXT NOT NULL, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY, user_id INTEGER, customer_name TEXT NOT NULL,
        customer_phone TEXT NOT NULL, order_type TEXT NOT NULL, delivery_address TEXT,
        delivery_time TEXT NOT NULL, tiffin_choice TEXT, tiffin_price REAL DEFAULT 0,
        extras_total REAL DEFAULT 0, grand_total REAL DEFAULT 0, status TEXT DEFAULT 'Pending Confirmation',
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT, item_name TEXT,
        item_type TEXT, quantity INTEGER, unit_price REAL, subtotal REAL
    )''')
    conn.commit()
    conn.close()

init_db()

def get_setting(key, default=""):
    conn = get_db()
    res = conn.execute("SELECT value FROM system_settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return res['value'] if res else default

def set_setting(key, value):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO system_settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

# --- HEADER BANNER ---
st.markdown("""
    <div class="brand-header">
        <div class="brand-title">ZEBA'S AUTHENTIC INDIAN TIFFIN SERVICE</div>
        <div class="brand-subtitle">Freshly Made | 100% Homemade | Healthy & Low Oil | Authentic Taste & Value</div>
        <div class="badge-bar">📞 Direct Orders & Enquiries: Zeba (07954 414208) | Tabrez (07914 076790)</div>
    </div>
""", unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION & PORTAL SWITCH ---
st.sidebar.title("Navigation")
portal = st.sidebar.radio("Select Portal:", ["📱 Customer Ordering Portal", "⚙️ Admin Management Portal"])

# --- PORTAL 1: CUSTOMER ORDERING PORTAL ---
if portal == "📱 Customer Ordering Portal":
    ordering_enabled = get_setting("ordering_enabled", "1") == "1"
    min_advance_hours = int(get_setting("min_advance_hours", "2"))
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Customer Authentication")
    
    if 'user' not in st.session_state:
        st.session_state.user = None
        
    if st.session_state.user is None:
        st.info("👋 **Please log in using your registered Phone Number & Password** (Account created by Admin Zeba/Tabrez).")
        
        col_log1, col_log2 = st.columns(2)
        with col_log1:
            login_phone = st.text_input("Registered Phone Number", placeholder="e.g. 07123456789")
            login_pass = st.text_input("Password", type="password")
            if st.button("Log In", type="primary"):
                conn = get_db()
                user = conn.execute("SELECT * FROM users WHERE phone=? AND password=?", (login_phone.strip(), login_pass.strip())).fetchone()
                conn.close()
                if user:
                    st.session_state.user = dict(user)
                    st.success(f"Welcome back, {user['name']}!")
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please contact Zeba/Tabrez if you need an account created.")
        
        with col_log2:
            st.markdown("#### Quick Demo Login")
            st.caption("Click below to test the ordering flow:")
            if st.button("Demo Login: Rahul (Monthly Subscriber)"):
                conn = get_db()
                u = conn.execute("SELECT * FROM users WHERE phone='07123456789'").fetchone()
                conn.close()
                if u:
                    st.session_state.user = dict(u)
                    st.rerun()
            if st.button("Demo Login: Priya (One-Time Buyer)"):
                conn = get_db()
                u = conn.execute("SELECT * FROM users WHERE phone='07987654321'").fetchone()
                conn.close()
                if u:
                    st.session_state.user = dict(u)
                    st.rerun()

    else:
        user = st.session_state.user
        
        today_str = datetime.now().strftime("%Y-%m-%d")
        is_active_sub = False
        if user['is_subscriber'] == 1 and user['sub_end_date']:
            if user['sub_end_date'] >= today_str:
                is_active_sub = True
                
        c_head1, c_head2, c_head3 = st.columns([2, 2, 1])
        with c_head1:
            st.markdown(f"### Welcome, **{user['name']}**")
            st.caption(f"Phone: {user['phone']} | Address: {user['address']}")
        with c_head2:
            if is_active_sub:
                st.markdown(f'<span class="sub-active">🟢 ACTIVE SUBSCRIBER (Valid till {user["sub_end_date"]})</span>', unsafe_allow_html=True)
                st.caption("✨ Daily Tiffin Box is covered at £0.00!")
            else:
                st.markdown('<span class="sub-inactive">🟠 ONE-TIME BUYER</span>', unsafe_allow_html=True)
                st.caption("Standard rates apply for daily tiffin.")
        with c_head3:
            if st.button("Log Out"):
                st.session_state.user = None
                st.rerun()

        st.markdown("---")

        if not ordering_enabled:
            st.error("🛑 **ORDERING IS CURRENTLY CLOSED FOR TODAY.** We are no longer accepting new orders right now. Please contact Zeba (07954 414208) or Tabrez (07914 076790) on WhatsApp directly for enquiries.")
        else:
            cust_tab1, cust_tab2 = st.tabs(["🛒 Place Tiffin & Ala Carte Order", "📜 My Order History & Status"])
            
            with cust_tab1:
                st.subheader("Step 1: Order Fulfillment & Delivery Time")
                
                c_ord1, c_ord2, c_ord3 = st.columns(3)
                with c_ord1:
                    order_type = st.radio("Fulfillment Type", ["Self Delivery", "Takeaway"], help="Select delivery or takeaway.")
                with c_ord2:
                    deliv_address = st.text_input("Delivery / Pickup Address", value=user['address'] if user['address'] else "High Street, London")
                with c_ord3:
                    min_time = datetime.now() + timedelta(hours=min_advance_hours)
                    default_time = min_time.strftime("%H:%M")
                    st.info(f"⏳ **Advance Lead Time:** Orders must be placed at least {min_advance_hours} hours in advance.")
                    delivery_time_str = st.text_input("Desired Delivery/Pickup Time", value=f"Today at {default_time}")

                st.markdown("---")
                st.subheader("Step 2: Dish of the Day (Fixed Tiffin Menu)")
                
                conn = get_db()
                dt = conn.execute("SELECT * FROM daily_tiffin ORDER BY id DESC LIMIT 1").fetchone()
                conn.close()
                veg_dish_today = dt['veg_dish'] if dt else "Paneer Butter Masala"
                non_veg_dish_today = dt['non_veg_dish'] if dt else "Chicken Korma"
                
                st.caption("The Tiffin Box includes: **2 Fresh Rotis/Phulkas + Basmati Rice + Main Curry + Homestyle Dal + Fresh Salad & Raita + Sweet**")
                
                tiffin_option = st.radio(
                    "Choose Daily Tiffin Box:",
                    [
                        "None (I only want Ala Carte / Snacks / Biryani)",
                        f"🥗 Veg Tiffin Box (Dish: {veg_dish_today})",
                        f"🍗 Non-Veg Tiffin Box (Dish: {non_veg_dish_today})"
                    ]
                )
                
                tiffin_price = 0.0
                tiffin_choice_name = "None"
                
                if "Veg Tiffin Box" in tiffin_option:
                    tiffin_choice_name = f"Veg Tiffin ({veg_dish_today})"
                    if is_active_sub:
                        tiffin_price = 0.0
                        st.success(f"✅ Covered by Monthly Subscription (£0.00)")
                    else:
                        tiffin_price = 6.00
                        st.markdown("**Price:** £6.00")
                elif "Non-Veg Tiffin Box" in tiffin_option:
                    tiffin_choice_name = f"Non-Veg Tiffin ({non_veg_dish_today})"
                    if is_active_sub:
                        tiffin_price = 0.0
                        st.success(f"✅ Covered by Monthly Subscription (£0.00)")
                    else:
                        tiffin_price = 7.00
                        st.markdown("**Price:** £7.00")

                st.markdown("---")
                st.subheader("Step 3: Ala Carte Specials, Snacks & Tiffin Extras")
                st.caption("💡 *Note: Ala carte extras, biryanis, and snacks are billed separately even for monthly subscribers.*")
                
                conn = get_db()
                items_db = conn.execute("SELECT * FROM menu_items WHERE is_available=1").fetchall()
                conn.close()
                
                biryanis = [i for i in items_db if i['category'] == 'Biryani']
                snacks = [i for i in items_db if i['category'] == 'Snack']
                extras = [i for i in items_db if i['category'] == 'Extra']
                
                selected_extras = {}
                
                cat_t1, cat_t2, cat_t3 = st.tabs(["🍗 Biryani Specials", "🥟 Snacks & Chaat", "🫓 Tiffin Add-ons & Extras"])
                
                with cat_t1:
                    for b in biryanis:
                        col_b1, col_b2, col_b3 = st.columns([3, 1, 1])
                        with col_b1:
                            st.markdown(f"**{b['name']}** — £{b['price']:.2f}")
                            st.caption(b['description'])
                        with col_b2:
                            qty = st.number_input(f"Qty ({b['name']})", min_value=0, max_value=10, value=0, key=f"item_{b['id']}")
                            if qty > 0:
                                selected_extras[b['name']] = {'qty': qty, 'price': b['price'], 'type': 'Biryani'}
                
                with cat_t2:
                    for s in snacks:
                        col_s1, col_s2, col_s3 = st.columns([3, 1, 1])
                        with col_s1:
                            st.markdown(f"**{s['name']}** — £{s['price']:.2f}")
                            st.caption(s['description'])
                        with col_s2:
                            qty = st.number_input(f"Qty ({s['name']})", min_value=0, max_value=10, value=0, key=f"item_{s['id']}")
                            if qty > 0:
                                selected_extras[s['name']] = {'qty': qty, 'price': s['price'], 'type': 'Snack'}

                with cat_t3:
                    for e in extras:
                        col_e1, col_e2, col_e3 = st.columns([3, 1, 1])
                        with col_e1:
                            st.markdown(f"**{e['name']}** — £{e['price']:.2f}")
                            st.caption(e['description'])
                        with col_e2:
                            qty = st.number_input(f"Qty ({e['name']})", min_value=0, max_value=10, value=0, key=f"item_{e['id']}")
                            if qty > 0:
                                selected_extras[e['name']] = {'qty': qty, 'price': e['price'], 'type': 'Extra'}

                st.markdown("---")
                st.subheader("Step 4: Order Summary & Review")
                
                extras_total = sum(item['qty'] * item['price'] for item in selected_extras.values())
                grand_total = tiffin_price + extras_total
                
                col_sum1, col_sum2 = st.columns(2)
                with col_sum1:
                    st.markdown("#### Itemized Breakdown:")
                    if tiffin_choice_name != "None":
                        if is_active_sub:
                            st.write(f"• **{tiffin_choice_name}**: £0.00 *(Covered by Subscription)*")
                        else:
                            st.write(f"• **{tiffin_choice_name}**: £{tiffin_price:.2f}")
                    else:
                        st.write("• *No daily tiffin selected*")
                        
                    for name, details in selected_extras.items():
                        sub = details['qty'] * details['price']
                        st.write(f"• **{name}** x{details['qty']}: £{sub:.2f}")
                        
                with col_sum2:
                    st.markdown("#### Total Payment Due:")
                    st.markdown(f"<div class='price-tag'>Grand Total: £{grand_total:.2f}</div>", unsafe_allow_html=True)
                    st.caption("ℹ️ *No in-app card payment required. Payment is collected upon delivery/pickup or logged under subscription ledger.*")

                st.markdown("---")
                
                if st.button("🚀 CONFIRM AND PLACE ORDER NOW", type="primary", use_container_width=True):
                    if tiffin_choice_name == "None" and len(selected_extras) == 0:
                        st.error("Please select at least one Tiffin, Biryani, Snack, or Extra item to place an order.")
                    else:
                        order_code = f"ZEBA-{datetime.now().strftime('%m%d%H%M%S')}"
                        conn = get_db()
                        conn.execute("""
                            INSERT INTO orders (order_id, user_id, customer_name, customer_phone, order_type, delivery_address, delivery_time, tiffin_choice, tiffin_price, extras_total, grand_total, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (order_code, user['id'], user['name'], user['phone'], order_type, deliv_address, delivery_time_str, tiffin_choice_name, tiffin_price, extras_total, grand_total, 'Pending Confirmation'))
                        
                        for name, details in selected_extras.items():
                            conn.execute("""
                                INSERT INTO order_items (order_id, item_name, item_type, quantity, unit_price, subtotal)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (order_code, name, details['type'], details['qty'], details['price'], details['qty'] * details['price']))
                            
                        conn.commit()
                        conn.close()
                        
                        st.balloons()
                        st.success(f"🎉 **Order Placed Successfully! Your Order ID is: `{order_code}`**")
                        
                        wa_msg = f"Hi Zeba & Tabrez, I have placed a new order!\n\nOrder ID: {order_code}\nCustomer: {user['name']} ({user['phone']})\nType: {order_type} ({delivery_time_str})\nAddress: {deliv_address}\nTiffin: {tiffin_choice_name}\nGrand Total: GBP {grand_total:.2f}\n\nPlease confirm my order!"
                        wa_url = f"https://wa.me/447954414208?text={wa_msg.replace(' ', '%20').replace('\n', '%0A')}"
                        
                        st.markdown(f'''
                            <a href="{wa_url}" target="_blank">
                                <button style="background-color:#25D366; color:white; font-size:18px; padding:12px 24px; border:none; border-radius:8px; cursor:pointer; width:100%; font-weight:bold;">
                                    📲 Click Here to Send Order Receipt to Zeba on WhatsApp
                                </button>
                            </a>
                        ''', unsafe_allow_html=True)

            with cust_tab2:
                st.subheader("My Past Orders & Real-time Tracker")
                conn = get_db()
                my_orders = conn.execute("SELECT * FROM orders WHERE user_id=? ORDER BY order_date DESC", (user['id'],)).fetchall()
                conn.close()
                
                if not my_orders:
                    st.info("You haven't placed any orders yet.")
                else:
                    for o in my_orders:
                        with st.expander(f"Order #{o['order_id']} — {o['order_date']} | Status: {o['status']}"):
                            st.write(f"**Status:** `{o['status']}`")
                            st.write(f"**Fulfillment:** {o['order_type']} ({o['delivery_time']})")
                            st.write(f"**Address:** {o['delivery_address']}")
                            st.write(f"**Tiffin Selection:** {o['tiffin_choice']}")
                            st.write(f"**Grand Total:** £{o['grand_total']:.2f}")
                            
                            conn = get_db()
                            items = conn.execute("SELECT * FROM order_items WHERE order_id=?", (o['order_id'],)).fetchall()
                            conn.close()
                            if items:
                                st.markdown("##### Extras & Snacks:")
                                for it in items:
                                    st.write(f" - {it['item_name']} x{it['quantity']} (£{it['subtotal']:.2f})")

# --- PORTAL 2: ADMIN MANAGEMENT PORTAL ---
else:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Admin Security")
    admin_pin = st.sidebar.text_input("Enter Admin PIN", type="password", value="")
    
    saved_pin = get_setting("admin_pin", "1234")
    
    if admin_pin != saved_pin:
        st.warning("🔐 Please enter the correct Admin PIN (Default: `1234`) to access the management portal.")
    else:
        st.success("🔓 **Admin Portal Unlocked** (Logged in as Zeba / Tabrez)")
        
        adm_tab1, adm_tab2, adm_tab3, adm_tab4, adm_tab5 = st.tabs([
            "⚡ Master & System Control",
            "🥗 Dish Availability (ON/OFF)",
            "👥 Customer & Subscription Manager",
            "📦 Live Orders & Status Update",
            "📊 Financial & User Order Ledger"
        ])
        
        with adm_tab1:
            st.subheader("Master System Controls")
            col_ctrl1, col_ctrl2 = st.columns(2)
            
            with col_ctrl1:
                cur_enabled = get_setting("ordering_enabled", "1") == "1"
                new_enabled = st.toggle("Start / Stop Ordering System Altogether", value=cur_enabled)
                if new_enabled != cur_enabled:
                    set_setting("ordering_enabled", "1" if new_enabled else "0")
                    st.success("Ordering status updated!")
                    st.rerun()
                if new_enabled:
                    st.success("🟢 System Status: OPEN FOR ORDERS")
                else:
                    st.error("🔴 System Status: CLOSED FOR ORDERS")
                    
            with col_ctrl2:
                cur_advance = int(get_setting("min_advance_hours", "2"))
                new_advance = st.number_input("Minimum Advance Lead Time (Hours)", min_value=1, max_value=24, value=cur_advance)
                if new_advance != cur_advance:
                    set_setting("min_advance_hours", new_advance)
                    st.success("Advance lead time updated!")

            st.markdown("---")
            st.subheader("Set Tiffin Dish of the Day")
            
            conn = get_db()
            dt = conn.execute("SELECT * FROM daily_tiffin ORDER BY id DESC LIMIT 1").fetchone()
            conn.close()
            
            cur_veg = dt['veg_dish'] if dt else "Paneer Butter Masala"
            cur_non_veg = dt['non_veg_dish'] if dt else "Chicken Korma"
            
            c_d1, c_d2 = st.columns(2)
            with c_d1:
                new_veg = st.text_input("Veg Dish of the Day", value=cur_veg)
            with c_d2:
                new_non_veg = st.text_input("Non-Veg Dish of the Day", value=cur_non_veg)
                
            if st.button("Save Dish of the Day"):
                conn = get_db()
                conn.execute("INSERT INTO daily_tiffin (date_type, veg_dish, non_veg_dish) VALUES ('Today', ?, ?)", (new_veg, new_non_veg))
                conn.commit()
                conn.close()
                st.success("Updated today's fixed tiffin menu!")

        with adm_tab2:
            st.subheader("Dish Availability Switch (ON / OFF)")
            st.caption("Turn dishes ON or OFF instantly if an item cannot be cooked or is out of stock.")
            
            conn = get_db()
            items = conn.execute("SELECT * FROM menu_items ORDER BY category, name").fetchall()
            conn.close()
            
            for it in items:
                c_i1, c_i2, c_i3 = st.columns([3, 1, 1])
                with c_i1:
                    st.write(f"**[{it['category']}] {it['name']}** (£{it['price']:.2f})")
                with c_i2:
                    is_avail = it['is_available'] == 1
                    toggle_status = st.toggle("Available", value=is_avail, key=f"avail_{it['id']}")
                    if toggle_status != is_avail:
                        conn = get_db()
                        conn.execute("UPDATE menu_items SET is_available=? WHERE id=?", (1 if toggle_status else 0, it['id']))
                        conn.commit()
                        conn.close()
                        st.rerun()

        with adm_tab3:
            st.subheader("Register New Customer & Manage Subscriptions")
            
            with st.expander("➕ Register New Customer Account (Create Credentials)"):
                with st.form("add_user_form"):
                    u_name = st.text_input("Customer Name")
                    u_phone = st.text_input("Phone Number (Login ID)")
                    u_pass = st.text_input("Set Password")
                    u_address = st.text_area("Delivery Address")
                    is_sub = st.checkbox("Enable Monthly Subscription?")
                    col_sub1, col_sub2 = st.columns(2)
                    with col_sub1:
                        sub_start = st.date_input("Subscription Start Date", value=datetime.now())
                    with col_sub2:
                        sub_end = st.date_input("Subscription End Date", value=datetime.now() + timedelta(days=30))
                        
                    submitted = st.form_submit_button("Create Account")
                    if submitted:
                        if not u_name or not u_phone or not u_pass:
                            st.error("Please fill in Name, Phone, and Password.")
                        else:
                            try:
                                conn = get_db()
                                conn.execute("""
                                    INSERT INTO users (name, phone, password, address, is_subscriber, sub_start_date, sub_end_date)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                """, (u_name, u_phone, u_pass, u_address, 1 if is_sub else 0, sub_start.strftime("%Y-%m-%d") if is_sub else None, sub_end.strftime("%Y-%m-%d") if is_sub else None))
                                conn.commit()
                                conn.close()
                                st.success(f"Customer account created for {u_name}!")
                            except Exception as e:
                                st.error(f"Error creating account (Phone number may already exist): {e}")

            st.markdown("#### Registered Customers & Subscription Status")
            conn = get_db()
            users_df = pd.read_sql_query("SELECT id, name, phone, password, is_subscriber, sub_start_date, sub_end_date, address FROM users", conn)
            conn.close()
            st.dataframe(users_df, use_container_width=True)

        with adm_tab4:
            st.subheader("Live Orders & Status Update")
            
            conn = get_db()
            orders_df = pd.read_sql_query("SELECT order_id, customer_name, customer_phone, order_type, delivery_time, tiffin_choice, grand_total, status, order_date FROM orders ORDER BY order_date DESC", conn)
            conn.close()
            
            if orders_df.empty:
                st.info("No orders placed yet.")
            else:
                for idx, row in orders_df.iterrows():
                    with st.expander(f"Order #{row['order_id']} | {row['customer_name']} | Status: {row['status']}"):
                        c_o1, c_o2 = st.columns(2)
                        with c_o1:
                            st.write(f"**Customer:** {row['customer_name']} ({row['customer_phone']})")
                            st.write(f"**Type:** {row['order_type']} | Time: {row['delivery_time']}")
                            st.write(f"**Tiffin:** {row['tiffin_choice']}")
                            st.write(f"**Total:** £{row['grand_total']:.2f}")
                        with c_o2:
                            new_status = st.selectbox(
                                "Update Status",
                                ["Pending Confirmation", "Confirmed", "In Preparation", "Out for Delivery", "Ready for Pickup", "Delivered / Completed", "Cancelled"],
                                index=["Pending Confirmation", "Confirmed", "In Preparation", "Out for Delivery", "Ready for Pickup", "Delivered / Completed", "Cancelled"].index(row['status']),
                                key=f"status_{row['order_id']}"
                            )
                            if new_status != row['status']:
                                conn = get_db()
                                conn.execute("UPDATE orders SET status=? WHERE order_id=?", (new_status, row['order_id']))
                                conn.commit()
                                conn.close()
                                st.success("Status updated!")
                                st.rerun()

        with adm_tab5:
            st.subheader("Financial & User-wise Order Ledger")
            
            conn = get_db()
            full_orders = pd.read_sql_query("""
                SELECT o.order_id, u.name as customer, u.is_subscriber, o.tiffin_choice, o.tiffin_price, o.extras_total, o.grand_total, o.status, o.order_date
                FROM orders o LEFT JOIN users u ON o.user_id = u.id
                ORDER BY o.order_date DESC
            """, conn)
            conn.close()
            
            if not full_orders.empty:
                tot_rev = full_orders['grand_total'].sum()
                tot_extras = full_orders['extras_total'].sum()
                
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("Total Revenue Collected", f"£{tot_rev:.2f}")
                col_m2.metric("Ala Carte Extra Revenue", f"£{tot_extras:.2f}")
                col_m3.metric("Total Orders Placed", len(full_orders))
                
                st.markdown("#### Detailed Order Log")
                st.dataframe(full_orders, use_container_width=True)
            else:
                st.info("No financial data recorded yet.")
