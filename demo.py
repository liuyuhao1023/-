import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO
import mysql.connector
import hashlib
from collections import Counter
import random
import math

st.set_page_config(page_title="出库调度系统", layout="wide")


if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'user' not in st.session_state:
    st.session_state.user = None
if 'main_page' not in st.session_state:
    st.session_state.main_page = '数据大屏'

# ======= 工具函数 =======
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_credentials(username, password):
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '1117',  # 修改为你的密码
        'database': 'login_system',
        'port': 3306
    }
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username=%s", (username,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0] == hash_password(password)
        return False
    except mysql.connector.Error as err:
        st.error(f"❌ 数据库连接失败: {err}")
        return False

def register_user(username, password):
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '1117',  # 修改为你的密码
        'database': 'login_system',
        'port': 3306
    }
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        if cursor.fetchone():
            conn.close()
            return False, "用户名已存在"
        hashed_pw = hash_password(password)
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_pw))
        conn.commit()
        conn.close()
        return True, "注册成功"
    except mysql.connector.Error as err:
        return False, f"数据库连接失败: {err}"


def login_page():
    st.title("🔐 登录系统")
    username = st.text_input("用户名")
    password = st.text_input("密码", type="password")
    if st.button("登录"):
        if check_credentials(username, password):
            st.session_state.user = username
            st.session_state.page = 'main'
            st.session_state.main_page = '数据大屏'
            st.success("登录成功")
            st.rerun()
        else:
            st.error("用户名或密码错误，或数据库连接失败")
    if st.button("没有账号？注册一个"):
        st.session_state.page = 'register'
        st.rerun()

def register_page():
    st.title("📝 注册账户")
    username = st.text_input("新用户名")
    password = st.text_input("新密码", type="password")
    confirm = st.text_input("确认密码", type="password")
    code = st.text_input("内部验证码")
    if st.button("注册"):
        if code != "88888888":
            st.error("内部验证码错误")
        elif password != confirm:
            st.error("两次密码不一致")
        elif username == "" or password == "":
            st.error("用户名或密码不能为空")
        else:
            success, msg = register_user(username, password)
            if success:
                st.success(msg)
                st.session_state.page = 'login'
                st.rerun()
            else:
                st.error(msg)
    if st.button("返回登录"):
        st.session_state.page = 'login'
        st.rerun()

def load_data():
    data_path = "bl_sku_合并结果.xlsx"
    sku_map_path = "最热销前4排+分区区内最优_订单驱动_库位分配结果.xlsx"
    df = pd.read_excel(data_path, dtype={"SKU编码": str})
    df.columns = df.columns.str.strip()
    df["SKU编码"] = df["SKU编码"].astype(str).str.zfill(4)
    if "库位" in df.columns:
        df["库位"] = df["库位"].astype(str).str.zfill(6)
    sku_map_df = pd.read_excel(sku_map_path, dtype={"SKU编码": str})
    sku_map_df["SKU编码"] = sku_map_df["SKU编码"].str.zfill(4)
    sku_map_df["库位"] = sku_map_df["库位"].astype(str).str.zfill(6)
    sku_map_df["排"] = sku_map_df["库位"].str[:2]
    sku_map_df["列"] = sku_map_df["库位"].str[2:4]
    sku_map_df["层"] = sku_map_df["库位"].str[4:6]
    sku_map_df["列号"] = sku_map_df["列"]
    sku_map = sku_map_df.set_index("SKU编码")["库位"].to_dict()
    sku_col_map = sku_map_df.set_index("SKU编码")["列号"].to_dict()
    sku_loc_map = sku_map_df.set_index("SKU编码")[["排", "列", "层"]].astype(int).to_dict(orient="index")
    df["下单日期"] = pd.to_datetime(df["下单日期"]).dt.date
    df["下单时间"] = pd.to_datetime(df["下单时间"].astype(str), format="%H:%M:%S", errors="coerce").dt.time
    df["下单时间戳"] = pd.to_datetime(df["下单日期"].astype(str) + " " + df["下单时间"].astype(str))
    return df, sku_map, sku_col_map, sku_loc_map

def main_app():
    
    st.sidebar.markdown(f"👤 当前用户：**{st.session_state.user}**")
    if st.sidebar.button("退出登录"):
        st.session_state.page = 'login'
        st.session_state.user = None
        st.rerun()

    main_page = st.sidebar.radio(
        "导航", 
        ("数据大屏", "出库明细", "调度与路径优化"),
        index=["数据大屏", "出库明细", "调度与路径优化"].index(st.session_state.main_page),
        key="main_page_radio"
    )
    st.session_state.main_page = main_page

    # 统一数据加载
    df, sku_map, sku_col_map, sku_loc_map = load_data()

    if main_page == "数据大屏":
        page_big_screen(df)
    elif main_page == "出库明细":
        page_table_detail(df, sku_map, sku_col_map)
    elif main_page == "调度与路径优化":
        page_scheduler(df, sku_loc_map)

def page_big_screen(df):
    # 如果你要白色页面，这一段 CSS 可以省略。如果要深色页面可保留/修改
    # st.markdown(
    #     """
    #     <style>
    #     .main { background-color: #18191a !important; color: #fff !important; }
    #     div[data-testid="stSidebar"] { background-color: #18191a !important; }
    #     </style>
    #     """,
    #     unsafe_allow_html=True
    # )
    st.title("📊 数据大屏")

    # ===== 默认参数 =====
    bigscreen_df = df.copy()
    bigscreen_df["下单年"] = pd.to_datetime(bigscreen_df["下单日期"]).dt.year
    bigscreen_df["下单月"] = pd.to_datetime(bigscreen_df["下单日期"]).dt.month
    bigscreen_df["下单日"] = pd.to_datetime(bigscreen_df["下单日期"]).dt.day
    bigscreen_df["下单周"] = pd.to_datetime(bigscreen_df["下单日期"]).dt.isocalendar().week
    bigscreen_df["下单季度"] = pd.to_datetime(bigscreen_df["下单日期"]).dt.quarter
    bigscreen_df["下单时"] = pd.to_datetime(bigscreen_df["下单时间"].astype(str), format="%H:%M:%S", errors="coerce").dt.hour

    # ====== 默认控件参数（只在首次刷新时赋值）======
    if "sku_bar_date" not in st.session_state:
        st.session_state["sku_bar_date"] = bigscreen_df["下单日期"].max()
    if "bigscreen_daterange" not in st.session_state:
        st.session_state["bigscreen_daterange"] = (bigscreen_df["下单日期"].min(), bigscreen_df["下单日期"].max())
    if "bigscreen_unit" not in st.session_state:
        st.session_state["bigscreen_unit"] = "天"

    # ============ 图表数据处理 ============


    # ============ 横向条形图：SKU每日出库量前10 ============
    sku_stat_day = st.session_state["sku_bar_date"]
    sku_rank_df = bigscreen_df[bigscreen_df["下单日期"] == sku_stat_day]

    # 保证SKU编码全部是字符串
    sku_rank_df["SKU编码"] = sku_rank_df["SKU编码"].astype(str)
    sku_rank = sku_rank_df.groupby("SKU编码")["出库数量"].sum().reset_index()
    sku_rank["SKU编码"] = sku_rank["SKU编码"].astype(str)  # 再转一次，彻底保险

    # 取出库量最多的10个SKU，并让最大值在y轴最上面
    sku_rank = sku_rank.sort_values("出库数量", ascending=False).head(10)
    sku_rank = sku_rank.sort_values("出库数量", ascending=True)

    # ***此时sku_rank一定已定义***，可以直接加前缀
    sku_rank["SKU显示"] = "SKU-" + sku_rank["SKU编码"]

    sku_bar_x = sku_rank["出库数量"].tolist()
    sku_bar_y = sku_rank["SKU显示"].tolist()  # 注意用"SKU显示"列

    sku_bar_title = f"SKU出库量排名（{sku_stat_day}）"

    # 2. 饼图和纵柱图
    start_date, end_date = st.session_state["bigscreen_daterange"]
    big_df = bigscreen_df[(bigscreen_df["下单日期"] >= start_date) & (bigscreen_df["下单日期"] <= end_date)].copy()
    unit = st.session_state["bigscreen_unit"]

    # 饼图
    pie_data = big_df.groupby("订单类别").size().reset_index(name="count")

    # 纵向柱状图
    if unit == "天":
        bar_group = big_df.groupby("下单日期")["出库数量"].sum().reset_index()
        bar_x = bar_group["下单日期"].astype(str)
        bar_y = bar_group["出库数量"]
        bar_title = "每日出库量"
    elif unit == "周":
        bar_group = big_df.groupby(["下单年", "下单周"])["出库数量"].sum().reset_index()
        bar_x = bar_group.apply(lambda x: f"{x['下单年']}年{int(x['下单周']):02d}周", axis=1)
        bar_y = bar_group["出库数量"]
        bar_title = "每周出库量"
    elif unit == "月":
        bar_group = big_df.groupby(["下单年", "下单月"])["出库数量"].sum().reset_index()
        bar_x = bar_group.apply(lambda x: f"{x['下单年']}年{int(x['下单月']):02d}月", axis=1)
        bar_y = bar_group["出库数量"]
        bar_title = "每月出库量"
    elif unit == "年":
        bar_group = big_df.groupby("下单年")["出库数量"].sum().reset_index()
        bar_x = bar_group["下单年"].astype(str)
        bar_y = bar_group["出库数量"]
        bar_title = "每年出库量"
    elif unit == "季度":
        bar_group = big_df.groupby(["下单年", "下单季度"])["出库数量"].sum().reset_index()
        bar_x = bar_group.apply(lambda x: f"{x['下单年']}年Q{int(x['下单季度'])}", axis=1)
        bar_y = bar_group["出库数量"]
        bar_title = "每季度出库量"
    elif unit == "小时":
        hour_group = big_df[(big_df["下单时"] >= 8) & (big_df["下单时"] <= 22)]
        bar_group = hour_group.groupby("下单时")["出库数量"].sum().reset_index()
        bar_x = bar_group["下单时"].astype(str)
        bar_y = bar_group["出库数量"]
        bar_title = "每天 8:00-22:00 每小时出库量"
    else:
        bar_x = []
        bar_y = []
        bar_title = "出库量"

    # ============ 画图 ============
    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        fig_pie = go.Figure(
            data=[go.Pie(
                labels=pie_data["订单类别"],
                values=pie_data["count"],
                hole=0.3
            )]
        )
        fig_pie.update_layout(
            title_text="订单类别占比",
            paper_bgcolor="rgba(0,0,0,0)",    # 透明背景
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#222",                # 黑色字体
            legend_font_color="#222"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    with row1_col2:
        fig_bar = go.Figure([go.Bar(x=bar_x, y=bar_y, marker_color='rgb(58,133,191)')])
        fig_bar.update_layout(
            title_text=bar_title,
            xaxis_title=unit,
            yaxis_title="出库数量",
            xaxis_tickangle=-45,
            barmode='group',
            height=420,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#222"     # 黑色字体
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    fig_sku_bar = go.Figure([
        go.Bar(
            x=sku_bar_x,
            y=sku_bar_y,
            orientation='h',
            marker=dict(
                color='rgba(255,127,14,0.9)',
                line=dict(color='rgba(0,0,0,0.5)', width=1.2)
            ),
            hovertemplate="SKU: %{y}<br>数量: %{x}<extra></extra>",
        )
    ])
    fig_sku_bar.update_layout(
        title_text=sku_bar_title,
        xaxis_title="出库数量",
        yaxis_title="SKU",
        height=max(440, 38 * len(sku_bar_y)),
        yaxis=dict(
            categoryorder='array',
            categoryarray=sku_bar_y,
            tickfont=dict(size=16, color="#222"),
            showgrid=False
        ),
        xaxis=dict(
            tickfont=dict(size=16, color="#222"),
            showgrid=False
        ),
        bargap=0,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#222"
    )
    st.markdown("### SKU出库量排名（横向条形图）")
    st.plotly_chart(fig_sku_bar, use_container_width=True)
    # ============ 控件集中到底部 ============
    st.markdown("---")
    with st.expander("数据大屏筛选"):
        col1, col2, col3 = st.columns(3)
        with col1:
            unique_days = bigscreen_df["下单日期"].sort_values().unique()
            sku_bar_date = st.date_input(
                "选择某一天SKU出库量排名",
                value=st.session_state["sku_bar_date"],
                min_value=unique_days[0] if len(unique_days) > 0 else None,
                max_value=unique_days[-1] if len(unique_days) > 0 else None,
                key="control_sku_bar_date"
            )
            st.session_state["sku_bar_date"] = sku_bar_date
        with col2:
            date_range = st.date_input(
                "选择统计日期范围（饼图/纵柱图）",
                value=st.session_state["bigscreen_daterange"],
                min_value=bigscreen_df["下单日期"].min(),
                max_value=bigscreen_df["下单日期"].max(),
                key="control_bigscreen_daterange"
            )
            if isinstance(date_range, tuple) or isinstance(date_range, list):
                st.session_state["bigscreen_daterange"] = date_range
            else:
                st.session_state["bigscreen_daterange"] = (date_range, date_range)
        with col3:
            unit = st.selectbox(
                "选择统计单位", ["天", "周", "月", "年", "小时", "季度"],
                index=["天", "周", "月", "年", "小时", "季度"].index(st.session_state["bigscreen_unit"]),
                key="control_bigscreen_unit"
            )
            st.session_state["bigscreen_unit"] = unit

        st.info("所有筛选均自动应用，顶部三个图实时更新。")



# ========== 业务页面2：出库明细 ==========
def page_table_detail(df, sku_map, sku_col_map,):
    st.title("📋 出库明细")
    st.markdown("#### 筛选条件")
    col1, col2, col3 = st.columns(3)
    with col1:
        start_ts, end_ts = st.date_input(
            "下单日期范围",
            [df["下单日期"].min(), df["下单日期"].max()],
            min_value=df["下单日期"].min(),
            max_value=df["下单日期"].max(),
            key="detail_daterange"
        )
    with col2:
        sku_search = st.text_input("🔍 搜索 SKU 编码", key="detail_sku")
    with col3:
        order_id_search = st.text_input("🔍 搜索订单编号", key="detail_orderid")
    mask = (df["下单日期"] >= start_ts) & (df["下单日期"] <= end_ts)
    filtered = df.loc[mask]
    if sku_search:
        pattern = sku_search.zfill(4)
        filtered = filtered[filtered["SKU编码"].str.contains(pattern, na=False)]
    if order_id_search:
        filtered = filtered[filtered["订单编号"].astype(str).str.contains(order_id_search.strip(), na=False)]
    st.dataframe(filtered, use_container_width=True)
    st.subheader("➕ 新增 / 删除出库数据")
    with st.expander("📥 添加新数据"):
        with st.form("add_form_detail"):
            new_order_id = st.text_input("订单编号")
            order_type = st.text_input("订单类别")
            order_date = st.date_input("下单日期", key="add_detail_date")
            order_time = st.time_input("下单时间", key="add_detail_time")
            sku_text = st.text_area("SKU及数量（格式：SKU1:数量1, SKU2:数量2）", value="0001:2, 0002:1")
            add_btn = st.form_submit_button("添加")
        if add_btn:
            try:
                sku_pairs = [s.strip().split(":") for s in sku_text.split(",") if ":" in s]
                new_rows = []
                for sku, qty in sku_pairs:
                    sku = sku.strip().zfill(4)
                    qty = int(qty)
                    if sku in sku_map:
                        new_rows.append({
                            "订单编号": new_order_id,
                            "SKU编码": sku,
                            "订单类别": order_type,
                            "下单日期": order_date,
                            "下单时间": order_time,
                            "下单时间戳": pd.to_datetime(f"{order_date} {order_time}"),
                            "库位": sku_map[sku],
                            "列号": sku_col_map.get(sku, None),
                            "出库数量": qty
                        })
                    else:
                        st.warning(f"⚠️ SKU {sku} 不存在于库位映射表中，未添加该条记录")
                if new_rows:
                    df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
                    df.to_excel("bl_sku_合并结果.xlsx", index=False)
                    st.success("✅ 数据添加成功，请刷新页面查看更新")
            except Exception as e:
                st.error(f"❌ 添加失败：{e}")
    with st.expander("🗑️ 删除指定订单"):
        del_order_id = st.text_input("输入要删除的订单编号").strip()
        if st.button("删除"):
            df["订单编号"] = df["订单编号"].astype(str).str.strip()
            before = len(df)
            df = df[df["订单编号"] != del_order_id]
            after = len(df)
            if after < before:
                df.to_excel("bl_sku_合并结果.xlsx", index=False)
                st.success(f"✅ 已删除订单编号为 {del_order_id} 的记录，请刷新页面查看更新")
            else:
                st.warning(f"⚠️ 未找到匹配的订单编号 “{del_order_id}”，请检查是否输入有误")

# ========== 业务页面3：调度与路径优化 ==========
def page_scheduler(df, sku_loc_map):
    st.title("🧮 调度与路径优化")

    # ========== 必须的全局参数 ==========
    ROW_DISTANCE = 2
    COL_DISTANCE = 1.4
    AISLES = [0, 35.5, 51]
    START_POS = (1, 1)
    efficiency = {
        "拣货员": {
            "熟练": {"查库": 10, "速度": 2.5, "登架": 30, "取货": 3, "卸货": 5, "扫码": 3, "打单": 240},
            "生疏": {"查库": 20, "速度": 1.5, "登架": 45, "取货": 5, "卸货": 8, "扫码": 5, "打单": 360},
        },
        "叉车员": {"默认": {"速度": 2.5}}
    }
    # 9组工人
    workers = {
        f"组{i+1}": {
            "拣货员": {"position": START_POS, "available_at": 0, "type": "熟练" if i < 7 else "生疏"},
            "叉车员": {"position": START_POS, "available_at": 0},
        }
        for i in range(9)
    }

    # --- 路径调度表单 ---
    st.subheader("📜 智能路径规划")
    num_orders = st.number_input("订单数量", min_value=1, max_value=10, value=2, step=1)
    orders = []
    with st.form("order_form"):
        for i in range(num_orders):
            st.markdown(f"### 订单{i+1}")
            order_id = st.text_input(f"订单编号_{i+1}", value=f"ORDER{i+1}")
            emergency = st.selectbox(f"紧急程度_{i+1}", ["高", "中", "低"], key=f"em_{i}")
            sku_input = st.text_area(f"SKU及数量（格式：SKU1:数量1, SKU2:数量2）_{i+1}", value="0001:2, 0002:1", key=f"skus_{i}")
            orders.append({"id": order_id, "emergency": emergency, "sku_text": sku_input})
        submitted = st.form_submit_button("提交并调度")

    # --- 路径调度算法 ---
    def simulated_annealing(points, start, end, distance_func, max_iter=1000, temp=1000, cooling_rate=0.995):
        if len(points) < 2:
            return points[:]
        current = points[:]
        best = current[:]
        def total_distance(path):
            full_path = [start] + path + [end]
            return sum(distance_func(full_path[i], full_path[i + 1]) for i in range(len(full_path) - 1))
        current_cost = total_distance(current)
        best_cost = current_cost
        for _ in range(max_iter):
            if len(current) < 2:
                break
            i, j = random.sample(range(len(current)), 2)
            new = current[:]
            new[i], new[j] = new[j], new[i]
            new_cost = total_distance(new)
            delta = new_cost - current_cost
            if delta < 0 or random.random() < math.exp(-delta / temp):
                current = new
                current_cost = new_cost
                if current_cost < best_cost:
                    best = current
                    best_cost = new_cost
            temp *= cooling_rate
        return best

    def compute_distance(p1, p2):
        row_dist = abs(int(p1[0]) - int(p2[0])) * ROW_DISTANCE
        col_dist = abs(int(p1[1]) - int(p2[1])) * COL_DISTANCE
        return math.sqrt(row_dist**2 + col_dist**2)

    def compute_realistic_path(p1, p2):
        r1, c1 = int(p1[0]), int(p1[1])
        r2, c2 = int(p2[0]), int(p2[1])
        path = [p1]
        if c1 == c2:
            path.append((r2, c2))
        else:
            min_path = None
            min_distance = float('inf')
            for aisle in AISLES:
                d = (
                    abs(c1 - aisle) * COL_DISTANCE +
                    abs(r1 - r2) * ROW_DISTANCE +
                    abs(c2 - aisle) * COL_DISTANCE
                )
                if d < min_distance:
                    min_distance = d
                    min_path = [
                        (r1, aisle),
                        (r2, aisle),
                        (r2, c2)
                    ]
            path.extend(min_path)
        return path

    def compute_full_path(points):
        full_path = []
        for i in range(len(points) - 1):
            segment = compute_realistic_path(points[i], points[i+1])
            if full_path:
                full_path.extend(segment[1:])
            else:
                full_path.extend(segment)
        return full_path

    def estimate_order_time(sku_list, start_pos, picker_type):
        p = efficiency["拣货员"][picker_type]
        valid_coords = []
        label_map = []
        for sku in sku_list:
            if sku in sku_loc_map:
                r, c = sku_loc_map[sku]['排'], sku_loc_map[sku]['列']
                valid_coords.append((r, c))
                label_map.append(f"{r:02}{c:02} ({sku})")
        optimized_coords = simulated_annealing(valid_coords, start_pos, START_POS, compute_distance)
        raw_path = [start_pos] + optimized_coords + [START_POS]
        full_path = compute_full_path(raw_path)
        walk_time = sum(
            compute_distance(full_path[i], full_path[i + 1]) / p['速度']
            for i in range(len(full_path) - 1)
        )
        op_time = len(valid_coords) * (p['查库'] + p['登架']) + len(sku_list) * (p['取货'] + p['卸货'] + p['扫码']) + p['打单']
        return walk_time + op_time, full_path, valid_coords, label_map

    def get_emergency_score(level):
        return {"高": 3, "中": 2, "低": 1}.get(level, 1)

    def assign_workers(orders):
        sorted_orders = sorted(orders, key=lambda x: -get_emergency_score(x['emergency']))
        results = []
        available_teams = list(workers.keys())
        for order in sorted_orders:
            sku_pairs = [s.strip().split(":") for s in order['sku_text'].split(",") if ":" in s]
            sku_list = []
            for sku, qty in sku_pairs:
                sku_list.extend([sku.strip().zfill(4)] * int(qty))
            min_total_time = float('inf')
            best_team = None
            for team in available_teams:
                picker = workers[team]['拣货员']
                start_pos = picker['position']
                time_needed, path, pick_points, labels = estimate_order_time(sku_list, start_pos, picker['type'])
                finish_time = picker['available_at'] + time_needed
                if finish_time < min_total_time:
                    min_total_time = finish_time
                    best_team = team
                    best_path = path
                    best_duration = time_needed
                    best_pick_points = pick_points
                    best_labels = labels
            if best_team:
                picker = workers[best_team]['拣货员']
                picker['available_at'] += best_duration
                picker['position'] = START_POS
                results.append({
                    "订单": order['id'],
                    "紧急程度": order['emergency'],
                    "拣货组": best_team,
                    "拣货员": best_team + "-拣货",
                    "预计完成时间": round(picker['available_at']/60, 2),
                    "拣货路径": best_path,
                    "取货点": best_pick_points,
                    "标签": best_labels,
                    "拣货员类型": picker['type'],
                    "SKU明细": sku_list
                })
                available_teams.remove(best_team)
        return results

    if submitted:
        schedule = assign_workers(orders)
        st.subheader("📋 调度结果")
        result_df = pd.DataFrame(schedule)[["订单", "紧急程度", "拣货组", "拣货员", "预计完成时间"]]
        if not result_df.empty:
            total_time_min = result_df["预计完成时间"].max()
            team_time = result_df.groupby("拣货组")["预计完成时间"].max().reset_index().rename(columns={"预计完成时间": "拣货组总工作时间（分钟）"})
            st.dataframe(team_time)
            st.info(f"⏱ 当前批次所有订单预计最晚完成时间：{total_time_min:.2f} 分钟")
        for s in schedule:
            st.markdown(f"#### 订单 {s['订单']} 路径")
            st.write(f"拣货组: {s['拣货组']}（{s['拣货员类型']}） | 预计完成时间: {s['预计完成时间']} 分钟")
            sku_counter = Counter(s['SKU明细'])
            sku_data = []
            for sku, qty in sku_counter.items():
                loc = sku_loc_map.get(sku, {})
                loc_str = f"{loc.get('排', '-')}-{loc.get('列', '-')}-{loc.get('层', '-')}"
                sku_data.append({"SKU编码": sku, "数量": qty, "库位": loc_str})
            sku_table = pd.DataFrame(sku_data)
            st.write("📦 SKU 拣货数量及库位：")
            st.dataframe(sku_table)
            path_df = pd.DataFrame(s['拣货路径'], columns=['排', '列'])
            pick_df = pd.DataFrame(s['取货点'], columns=['排', '列'])
            labels = s['标签']
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=path_df['列'], y=path_df['排'],
                mode='lines+markers', marker=dict(size=6, color='green'),
                line=dict(color='lightgreen', width=2), name='路径'
            ))
            fig.add_trace(go.Scatter(
                x=pick_df['列'], y=pick_df['排'],
                mode='markers+text', marker=dict(size=10, color='yellow'),
                text=labels, textposition='top center', name='取货点'
            ))
            fig.add_trace(go.Scatter(
                x=[path_df.iloc[0]['列']], y=[path_df.iloc[0]['排']],
                mode='markers+text', marker=dict(size=12, color='green'),
                text=['起点'], textposition='bottom center', name='起点'
            ))
            fig.add_trace(go.Scatter(
                x=[path_df.iloc[-1]['列']], y=[path_df.iloc[-1]['排']],
                mode='markers+text', marker=dict(size=12, color='red'),
                text=['终点'], textposition='bottom center', name='终点'
            ))
            fig.update_layout(
                title=f"订单 {s['订单']} 拣货路径图",
                xaxis=dict(title="列", dtick=2),
                yaxis=dict(title="排", autorange=True, dtick=1),
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)
##### 最后是路由入口 #####
if st.session_state.page == 'login':
    login_page()
elif st.session_state.page == 'register':
    register_page()
elif st.session_state.page == 'main':
    main_app()