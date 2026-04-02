# 出库调度系统 - WMS 智能管理平台

## 📋 项目简介

这是一个基于 Streamlit 开发的仓库管理系统（WMS），专为物流方案设计大赛设计。系统实现了用户认证、数据可视化、出库明细管理和智能路径优化等功能，帮助仓库实现高效的出库调度和库位管理。

## ✨ 功能特性

### 🔐 用户认证系统

- 用户登录/注册功能
- 密码加密存储（SHA256）
- 基于 Session 的状态管理

### 📊 数据大屏

- 订单类别占比饼图
- 多时间维度统计（天/周/月/年/小时/季度）
- SKU 出库量排名可视化（横向条形图）
- 实时数据筛选和动态更新

### 📋 出库明细管理

- 订单数据查询和筛选
- 支持按日期范围、SKU 编码、订单编号搜索
- 新增出库数据功能
- 删除指定订单记录

### 🧮 智能路径优化

- 多订单批量调度
- 模拟退火算法优化拣货路径
- 考虑多种因素：查库时间、行走速度、登架时间、取货时间、卸货时间、扫码时间、打单时间
- 支持熟练/生疏拣货员配置
- 9组工人并行调度

## 🛠️ 技术栈

### 前端框架

- **Streamlit**: Web 应用框架
- **Plotly**: 交互式数据可视化

### 数据处理

- **Pandas**: 数据分析和处理
- **openpyxl**: Excel 文件读写

### 数据库

- **MySQL**: 用户认证和数据存储
- **mysql-connector-python**: MySQL 连接器

### 算法

- 模拟退火算法（Simulated Annealing）
- 贪婪算法（Greedy Algorithm）

## 📦 安装依赖

### 方法一：使用 pip 安装

```bash
pip install -r requirements.txt
```

### 方法二：手动安装

```bash
pip install streamlit pandas plotly mysql-connector-python openpyxl
```

## 🗄️ 数据库配置

### 1. 创建数据库

```sql
CREATE DATABASE login_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 创建用户表

```sql
USE login_system;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. 配置数据库连接

在 `demo.py` 文件中修改数据库配置：

```python
DB_CONFIG = {
    'host': 'localhost',      # 数据库地址
    'user': 'root',           # 数据库用户名
    'password': '1117',       # 数据库密码
    'database': 'login_system',
    'port': 3306
}
```

## 📂 项目结构

```
案例7附件/
├── demo.py                          # 主程序文件
├── requirements.txt                 # Python 依赖包
├── README.md                        # 项目说明文档
├── bl_sku_合并结果.xlsx             # 出库数据文件
└── 最热销前4排+分区区内最优_订单驱动_库位分配结果.xlsx  # 库位映射文件
```

## ▶️ 运行项目

### 前置条件

- Python 3.8+
- MySQL 5.7+ 或 MySQL 8.0+
- 已安装所有依赖包

### 启动步骤

1. **启动 MySQL 数据库**

   ```bash
   # 确保 MySQL 服务正在运行
   # 确保已创建数据库和用户表
   ```
2. **准备数据文件**

   - 确保 `bl_sku_合并结果.xlsx` 和 `最热销前4排+分区区内最优_订单驱动_库位分配结果.xlsx` 在同一目录下
3. **运行应用**

   ```bash
   streamlit run demo.py
   ```
4. **访问应用**

   - 打开浏览器访问 `http://localhost:8501`

## 🎯 使用说明

### 1. 注册账号

- 首次使用需要注册账号
- 内部验证码：`88888888`

### 2. 数据大屏

- 查看订单类别占比
- 分析出库量趋势
- 查看 SKU 出库量排名
- 支持多时间维度筛选

### 3. 出库明细

- 查询历史出库记录
- 添加新的出库订单
- 删除不需要的订单

### 4. 调度与路径优化

- 输入多个订单信息
- 设置订单紧急程度
- 配置 SKU 及数量
- 系统自动优化拣货路径

## 🔧 参数配置

### 仓库参数（在 `demo.py` 中配置）

```python
ROW_DISTANCE = 2        # 排间距（米）
COL_DISTANCE = 1.4      # 列间距（米）
AISLES = [0, 35.5, 51]  # 通道位置
START_POS = (1, 1)      # 起始位置
```

### 工作效率参数

```python
efficiency = {
    "拣货员": {
        "熟练": {
            "查库": 10,    # 秒/次
            "速度": 2.5,   # 米/秒
            "登架": 30,    # 秒/次
            "取货": 3,     # 秒/次
            "卸货": 5,     # 秒/次
            "扫码": 3,     # 秒/次
            "打单": 240    # 秒/单
        },
        "生疏": {...}
    },
    "叉车员": {...}
}
```

## 📊 数据文件格式

### bl_sku_合并结果.xlsx

| 字段     | 说明         |
| -------- | ------------ |
| 订单编号 | 订单唯一标识 |
| SKU编码  | 商品编码     |
| 订单类别 | 订单类型     |
| 下单日期 | 下单日期     |
| 下单时间 | 下单时间     |
| 出库数量 | 出库数量     |

### 最热销前4排+分区区内最优_订单驱动_库位分配结果.xlsx

| 字段    | 说明                     |
| ------- | ------------------------ |
| SKU编码 | 商品编码                 |
| 库位    | 库位编号（格式：排列层） |
| 排      | 库位排号                 |
| 列      | 库位列号                 |
| 层      | 库位层号                 |

## 🐛 常见问题

### 1. 数据库连接失败

- 检查 MySQL 服务是否启动
- 确认数据库配置是否正确
- 确认数据库和表是否已创建

### 2. Excel 文件读取失败

- 确认文件路径正确
- 检查文件格式是否为 `.xlsx`
- 确认文件未被其他程序占用

### 3. 端口被占用

```bash
# 查找占用端口的进程
netstat -ano | findstr :8501
# 或使用其他端口
streamlit run demo.py --server.port 8502
```

## 📝 开发说明

### 代码结构

- `login_page()`: 登录页面
- `register_page()`: 注册页面
- `main_app()`: 主应用入口
- `page_big_screen()`: 数据大屏页面
- `page_table_detail()`: 出库明细页面
- `page_scheduler()`: 调度与路径优化页面

### 算法说明

- **模拟退火算法**: 用于路径优化，避免陷入局部最优
- **贪心算法**: 用于初始路径生成
- 考虑多种作业时间，综合优化总作业时间

## 📄 许可证

本项目仅用于参赛使用。

## 🙏 致谢

感谢为本项目提供支持和帮助的老师、同学和团队成员！
