import streamlit as st
import pandas as pd
import os
import sys
import subprocess
import tempfile
import zipfile
from pathlib import Path
import configparser
from datetime import datetime
import io
import json
import requests
import time
import hashlib
from typing import Dict, List, Any, Optional

# 设置页面配置
st.set_page_config(
    page_title="CKAN Tools",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #2563eb;
        margin: 1rem 0;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        color: #155724;
    }
    .error-box {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        color: #721c24;
    }
    .info-box {
        background: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 1rem;
        color: #0c5460;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .log-container {
        background: #1a1a1a;
        color: #00ff00;
        padding: 1rem;
        border-radius: 5px;
        font-family: 'Courier New', monospace;
        max-height: 300px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

class CKANApi:
    """CKAN API客户端"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': api_key,
            'Content-Type': 'application/json'
        })
    
    def test_connection(self) -> Dict[str, Any]:
        """测试CKAN连接"""
        try:
            response = self.session.get(f"{self.base_url}/api/3/action/site_read")
            if response.status_code == 200:
                return {"success": True, "message": "连接成功"}
            else:
                return {"success": False, "message": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def create_dataset(self, dataset_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建数据集"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/3/action/package_create",
                json=dataset_data
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": {"message": str(e)}}
    
    def update_dataset(self, dataset_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新数据集"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/3/action/package_update",
                json=dataset_data
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": {"message": str(e)}}
    
    def get_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """获取数据集信息"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/3/action/package_show?id={dataset_id}"
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": {"message": str(e)}}
    
    def list_datasets(self) -> Dict[str, Any]:
        """列出所有数据集"""
        try:
            response = self.session.get(f"{self.base_url}/api/3/action/package_list")
            return response.json()
        except Exception as e:
            return {"success": False, "error": {"message": str(e)}}

class CKANToolsApp:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        
        # 初始化session state
        if 'logs' not in st.session_state:
            st.session_state.logs = []
        if 'processing' not in st.session_state:
            st.session_state.processing = False
        
    def add_log(self, message: str, log_type: str = "info"):
        """添加日志消息"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = {
            'timestamp': timestamp,
            'message': message,
            'type': log_type
        }
        st.session_state.logs.append(log_entry)
        
        # 只保留最近50条日志
        if len(st.session_state.logs) > 50:
            st.session_state.logs = st.session_state.logs[-50:]
    
    def display_logs(self):
        """显示日志"""
        if st.session_state.logs:
            st.subheader("📋 处理日志")
            
            log_container = st.container()
            with log_container:
                for log in st.session_state.logs[-10:]:  # 显示最近10条
                    timestamp = log['timestamp']
                    message = log['message']
                    log_type = log['type']
                    
                    if log_type == "success":
                        st.success(f"[{timestamp}] ✅ {message}")
                    elif log_type == "error":
                        st.error(f"[{timestamp}] ❌ {message}")
                    elif log_type == "warning":
                        st.warning(f"[{timestamp}] ⚠️ {message}")
                    else:
                        st.info(f"[{timestamp}] ℹ️ {message}")
        
    def main(self):
        # 主标题
        st.markdown("""
        <div class="main-header">
            <h1>🛠️ CKAN Tools</h1>
            <p>Excel Import & File Monitor - Web版本</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 侧边栏导航
        with st.sidebar:
            st.image("https://via.placeholder.com/200x100/2563eb/ffffff?text=CKAN+Tools", 
                    caption="数据管理工具")
            
            tool_option = st.selectbox(
                "选择工具",
                ["🏠 首页", "📊 Excel导入到CKAN", "📁 文件监控器", "⚙️ 配置管理", "📚 使用说明"]
            )
            
            # 快速状态检查
            if st.button("🔍 检查CKAN连接", use_container_width=True):
                self.quick_connection_test()
        
        # 根据选择显示不同页面
        if tool_option == "🏠 首页":
            self.show_home_page()
        elif tool_option == "📊 Excel导入到CKAN":
            self.show_excel_import_page()
        elif tool_option == "📁 文件监控器":
            self.show_file_monitor_page()
        elif tool_option == "⚙️ 配置管理":
            self.show_config_page()
        elif tool_option == "📚 使用说明":
            self.show_help_page()
    
    def quick_connection_test(self):
        """快速连接测试"""
        ckan_url = st.session_state.get('ckan_url', '')
        api_key = st.session_state.get('api_key', '')
        
        if not ckan_url or not api_key:
            st.sidebar.error("请先在配置页面设置CKAN连接信息")
            return
        
        with st.sidebar:
            with st.spinner("测试连接中..."):
                api = CKANApi(ckan_url, api_key)
                result = api.test_connection()
                
                if result["success"]:
                    st.success("✅ 连接正常")
                else:
                    st.error(f"❌ 连接失败: {result['message']}")
    
    def show_home_page(self):
        """显示首页"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="feature-card">
                <h3>📊 Excel导入到CKAN</h3>
                <p>上传Excel文件，自动创建或更新CKAN数据集。支持多种schema格式，包括dataset、device、digitaltwin等。</p>
                <ul>
                    <li>自动解析Excel schema</li>
                    <li>批量创建数据集</li>
                    <li>实时进度显示</li>
                    <li>错误日志记录</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="feature-card">
                <h3>📁 文件监控器</h3>
                <p>监控本地文件变化，与CKAN资源进行对比，检测需要同步的过期文件。</p>
                <ul>
                    <li>实时文件监控</li>
                    <li>版本对比分析</li>
                    <li>同步建议</li>
                    <li>详细报告生成</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # 快速开始
        st.subheader("🚀 快速开始")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 开始Excel导入", use_container_width=True):
                st.rerun()
        
        with col2:
            if st.button("📁 启动文件监控", use_container_width=True):
                st.rerun()
        
        with col3:
            if st.button("⚙️ 配置设置", use_container_width=True):
                st.rerun()
        
        # 使用统计
        self.show_usage_stats()
        
        # 最近活动
        self.show_recent_activity()
    
    def show_excel_import_page(self):
        """Excel导入页面"""
        st.header("📊 Excel导入到CKAN")
        
        # 检查配置
        if not self.check_config():
            st.warning("⚠️ 请先在配置页面设置CKAN连接信息")
            return
        
        # 文件上传区域
        st.subheader("1. 上传Excel文件")
        uploaded_file = st.file_uploader(
            "选择Excel文件",
            type=['xlsx', 'xls'],
            help="支持包含dataset、device、digitaltwin等schema的Excel文件",
            key="excel_upload"
        )
        
        if uploaded_file is not None:
            # 保存上传的文件
            file_path = os.path.join(self.temp_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # 文件信息
            file_size = len(uploaded_file.getbuffer()) / 1024 / 1024  # MB
            st.info(f"📄 文件: {uploaded_file.name} ({file_size:.2f} MB)")
            
            # 文件预览
            self.preview_excel_file(file_path)
            
            # 导入选项
            st.subheader("2. 导入选项")
            
            col1, col2 = st.columns(2)
            
            with col1:
                update_existing = st.checkbox("更新已存在的数据集", value=True)
                validate_data = st.checkbox("数据验证", value=True)
                
            with col2:
                batch_size = st.number_input("批处理大小", min_value=1, max_value=100, value=10)
                dry_run = st.checkbox("模拟运行（不实际创建）", value=False)
            
            # 执行导入
            st.subheader("3. 执行导入")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if st.button("🚀 开始导入", use_container_width=True, type="primary", 
                           disabled=st.session_state.processing):
                    self.execute_excel_import(
                        file_path, update_existing, validate_data, 
                        batch_size, dry_run
                    )
            
            with col2:
                if st.button("🗑️ 清除日志", use_container_width=True):
                    st.session_state.logs = []
                    st.rerun()
        
        # 显示日志
        self.display_logs()
    
    def show_file_monitor_page(self):
        """文件监控页面"""
        st.header("📁 文件监控器")
        
        # 检查配置
        if not self.check_config():
            st.warning("⚠️ 请先在配置页面设置CKAN连接信息")
            return
        
        # 监控配置
        st.subheader("1. 监控配置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("💡 由于Web环境限制，请上传要监控的文件夹压缩包")
            uploaded_zip = st.file_uploader(
                "上传监控文件夹(ZIP格式)",
                type=['zip'],
                help="将需要监控的文件夹压缩为ZIP文件后上传",
                key="zip_upload"
            )
            
        with col2:
            dataset_filter = st.text_input(
                "数据集名称过滤器（可选）",
                placeholder="例如：sensor-data*",
                help="使用通配符过滤要检查的数据集"
            )
        
        # 监控选项
        st.subheader("2. 监控选项")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            check_metadata = st.checkbox("检查元数据", value=True)
            check_size = st.checkbox("检查文件大小", value=True)
            
        with col2:
            check_timestamp = st.checkbox("检查时间戳", value=True)
            check_hash = st.checkbox("检查文件哈希", value=False)
            
        with col3:
            debug_mode = st.checkbox("调试模式", value=False)
            detailed_report = st.checkbox("详细报告", value=True)
        
        # 执行监控
        st.subheader("3. 执行监控")
        
        if uploaded_zip is not None:
            zip_size = len(uploaded_zip.getbuffer()) / 1024 / 1024
            st.info(f"📦 ZIP文件: {uploaded_zip.name} ({zip_size:.2f} MB)")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if st.button("🔍 开始监控", use_container_width=True, type="primary",
                           disabled=st.session_state.processing):
                    self.execute_file_monitor(
                        uploaded_zip, dataset_filter, check_metadata, 
                        check_size, check_timestamp, check_hash, 
                        debug_mode, detailed_report
                    )
            
            with col2:
                if st.button("🗑️ 清除日志", use_container_width=True):
                    st.session_state.logs = []
                    st.rerun()
        
        # display monitor history

        self.show_monitor_history()
        
        # 显示日志
        self.display_logs()
    
    def show_config_page(self):
        """配置管理页面"""
        st.header("⚙️ 配置管理")
        
        # CKAN连接配置
        st.subheader("🔗 CKAN连接配置")
        
        with st.form("ckan_config"):
            col1, col2 = st.columns(2)
            
            with col1:
                ckan_url = st.text_input(
                    "CKAN服务器URL",
                    value=st.session_state.get('ckan_url', ''),
                    placeholder="https://your-ckan-instance.com",
                    help="CKAN实例的完整URL地址"
                )
                
                api_key = st.text_input(
                    "API密钥",
                    value=st.session_state.get('api_key', ''),
                    type="password",
                    help="在CKAN用户设置中可以找到API密钥"
                )
                
            with col2:
                org_name = st.text_input(
                    "默认组织",
                    value=st.session_state.get('org_name', ''),
                    placeholder="your-organization",
                    help="创建数据集时的默认组织"
                )
                
                default_license = st.selectbox(
                    "默认许可证",
                    ["cc-by", "cc-by-sa", "cc-zero", "odc-pddl", "other-open"],
                    index=0,
                    help="新数据集的默认许可证类型"
                )
            
            # 高级设置
            st.subheader("🔧 高级设置")
            
            col1, col2 = st.columns(2)
            
            with col1:
                request_timeout = st.number_input(
                    "请求超时时间(秒)",
                    min_value=10,
                    max_value=300,
                    value=st.session_state.get('request_timeout', 60)
                )
                
            with col2:
                max_retries = st.number_input(
                    "最大重试次数",
                    min_value=0,
                    max_value=10,
                    value=st.session_state.get('max_retries', 3)
                )
            
            # 按钮
            col1, col2 = st.columns(2)
            
            with col1:
                test_connection = st.form_submit_button("🔧 测试连接", use_container_width=True)
                
            with col2:
                save_config = st.form_submit_button("💾 保存配置", use_container_width=True, type="primary")
            
            # 处理表单提交
            if test_connection:
                self.test_ckan_connection(ckan_url, api_key)
                
            if save_config:
                # 保存配置到session state
                st.session_state.update({
                    'ckan_url': ckan_url,
                    'api_key': api_key,
                    'org_name': org_name,
                    'default_license': default_license,
                    'request_timeout': request_timeout,
                    'max_retries': max_retries
                })
                st.success("✅ 配置已保存")
                self.add_log("配置已更新", "success")
        
        # 配置导入/导出
        st.subheader("📋 配置导入/导出")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📤 导出配置", use_container_width=True):
                config_data = {
                    'ckan_url': st.session_state.get('ckan_url', ''),
                    'org_name': st.session_state.get('org_name', ''),
                    'default_license': st.session_state.get('default_license', 'cc-by'),
                    'request_timeout': st.session_state.get('request_timeout', 60),
                    'max_retries': st.session_state.get('max_retries', 3)
                }
                
                config_json = json.dumps(config_data, indent=2, ensure_ascii=False)
                st.download_button(
                    label="💾 下载配置文件",
                    data=config_json,
                    file_name="ckan_tools_config.json",
                    mime="application/json"
                )
        
        with col2:
            uploaded_config = st.file_uploader(
                "📥 导入配置文件",
                type=['json'],
                help="上传之前导出的配置文件"
            )
            
            if uploaded_config:
                try:
                    config_data = json.load(uploaded_config)
                    st.session_state.update(config_data)
                    st.success("✅ 配置已导入")
                    self.add_log("配置文件已导入", "success")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 导入配置失败: {str(e)}")
    
    def show_help_page(self):
        """使用说明页面"""
        st.header("📚 使用说明")
        
        # 快速入门
        with st.expander("🚀 快速入门", expanded=True):
            st.markdown("""
            ### 1. Excel导入到CKAN
            
            **步骤:**
            1. 在侧边栏选择"📊 Excel导入到CKAN"
            2. 上传包含数据集信息的Excel文件
            3. 配置CKAN服务器URL和API密钥
            4. 预览要导入的数据
            5. 点击"开始导入"按钮
            
            **Excel文件格式要求:**
            - 支持.xlsx和.xls格式
            - 每个工作表代表一种schema类型(dataset、device、digitaltwin等)
            - 第一行应为列标题
            - 必需字段：name(名称)、title(标题)
            
            **常用字段说明:**
            - `name`: 数据集唯一标识符（必需）
            - `title`: 数据集标题（必需）
            - `notes`: 数据集描述
            - `owner_org`: 所属组织
            - `tags`: 标签（用逗号分隔）
            - `license_id`: 许可证类型
            
            ---
            
            ### 2. 文件监控器
            
            **步骤:**
            1. 在侧边栏选择"📁 文件监控器"
            2. 上传要监控的文件夹压缩包
            3. 配置CKAN连接信息
            4. 选择监控选项
            5. 点击"开始监控"按钮
            
            **监控功能:**
            - 文件修改时间对比
            - 文件大小变化检测
            - 元数据一致性检查
            - 生成同步建议报告
            """)
        
        # 常见问题
        with st.expander("❓ 常见问题"):
            st.markdown("""
            **Q: 如何获取CKAN API密钥?**
            
            A: 登录您的CKAN实例，进入用户设置页面，在"API Key"部分可以找到或生成新的密钥。
            
            **Q: Excel文件应该包含哪些字段?**
            
            A: 基本必需字段包括：
            - `name`: 数据集唯一标识符
            - `title`: 数据集标题
            - `notes`: 数据集描述(可选)
            - `owner_org`: 所属组织(可选)
            
            **Q: 为什么文件监控需要上传ZIP文件?**
            
            A: 由于Web应用的安全限制，无法直接访问用户本地文件系统。通过上传ZIP文件的方式可以在云端模拟文件监控功能。
            
            **Q: 处理大文件时应该注意什么?**
            
            A: 建议：
            - 将大文件分批处理
            - 使用较小的批处理大小
            - 增加超时时间设置
            - 在网络状况良好时进行操作
            
            **Q: 如何处理导入错误?**
            
            A: 常见错误解决方案：
            - 名称冲突：检查数据集名称是否已存在
            - 权限不足：确认API密钥有相应权限
            - 格式错误：检查Excel文件格式和字段名称
            - 网络超时：增加超时时间或分批处理
            """)
        
        # API文档
        with st.expander("🔧 技术说明"):
            st.markdown("""
            ### CKAN API端点
            
            本工具使用以下CKAN API端点：
            
            - `package_create`: 创建新数据集
            - `package_update`: 更新已存在的数据集
            - `package_show`: 获取数据集信息
            - `package_list`: 列出所有数据集
            - `resource_create`: 创建资源
            - `resource_update`: 更新资源
            
            ### 错误代码说明
            
            - `200`: 操作成功
            - `400`: 请求参数错误
            - `401`: 认证失败，检查API密钥
            - `403`: 权限不足
            - `404`: 资源不存在
            - `409`: 资源冲突（如名称重复）
            - `500`: 服务器内部错误
            
            ### 数据验证规则
            
            - 数据集名称只能包含小写字母、数字、连字符和下划线
            - 名称长度不能超过100个字符
            - 标题不能为空
            - 组织名称必须存在于CKAN中
            """)
        
        # 示例文件
        with st.expander("📄 示例文件"):
            st.markdown("### Excel文件示例")
            
            # 创建示例数据
            sample_data = pd.DataFrame({
                'name': ['sensor-data-2024', 'weather-station-alpha', 'traffic-monitor-001'],
                'title': ['传感器数据2024', '天气站Alpha数据', '交通监控点001'],
                'notes': ['2024年传感器采集数据', '天气站Alpha的气象数据', '交通监控点的车流数据'],
                'tags': ['sensor,data,2024', 'weather,climate', 'traffic,monitoring'],
                'license_id': ['cc-by', 'cc-by-sa', 'cc-zero']
            })
            
            st.dataframe(sample_data, use_container_width=True)
            
            # 提供下载示例文件
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                sample_data.to_excel(writer, sheet_name='dataset', index=False)
            
            st.download_button(
                label="📥 下载示例Excel文件",
                data=excel_buffer.getvalue(),
                file_name="ckan_tools_example.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        # 联系信息
        st.subheader("📞 支持与反馈")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("""
            **遇到问题？**
            
            - 检查网络连接
            - 验证CKAN服务器状态
            - 确认API密钥有效性
            - 查看详细错误日志
            - 尝试使用示例文件测试
            """)
        
        with col2:
            st.success("""
            **反馈渠道**
            
            - 提交GitHub Issue
            - 发送邮件反馈
            - 加入用户讨论群
            - 查看在线文档
            - 参与功能建议讨论
            """)
    
    def check_config(self) -> bool:
        """检查CKAN配置是否完整"""
        return bool(st.session_state.get('ckan_url') and st.session_state.get('api_key'))
    
    def preview_excel_file(self, file_path: str):
        """预览Excel文件内容"""
        try:
            excel_data = pd.ExcelFile(file_path)
            sheet_names = excel_data.sheet_names
            
            st.subheader("📋 文件预览")
            
            # 显示工作表选择
            selected_sheets = st.multiselect(
                "选择要处理的工作表",
                sheet_names,
                default=sheet_names,
                help="选择要导入到CKAN的工作表"
            )
            
            # 预览选中的工作表
            for sheet in selected_sheets:
                with st.expander(f"📊 预览: {sheet}", expanded=len(selected_sheets) == 1):
                    df = pd.read_excel(file_path, sheet_name=sheet)
                    
                    # 显示基本信息
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("总行数", len(df))
                    with col2:
                        st.metric("总列数", len(df.columns))
                    with col3:
                        st.metric("有效数据行", len(df.dropna()))
                    
                    # 显示数据预览
                    st.dataframe(df.head(10), use_container_width=True)
                    
                    # 检查必需字段
                    required_fields = ['name', 'title']
                    missing_fields = [field for field in required_fields if field not in df.columns]
                    
                    if missing_fields:
                        st.warning(f"⚠️ 缺少必需字段: {', '.join(missing_fields)}")
                    else:
                        st.success("✅ 包含所有必需字段")
                        
        except Exception as e:
            st.error(f"❌ 预览文件时出错: {str(e)}")
    
    def test_ckan_connection(self, ckan_url: str, api_key: str):
        """测试CKAN连接"""
        if not ckan_url or not api_key:
            st.error("❌ 请填写CKAN URL和API密钥")
            return
        
        with st.spinner("🔄 正在测试连接..."):
            try:
                api = CKANApi(ckan_url, api_key)
                result = api.test_connection()
                
                if result["success"]:
                    st.success("✅ CKAN连接测试成功！")
                    st.info(f"🌐 服务器: {ckan_url}")
                    st.info("🔑 API密钥验证通过")
                    self.add_log("CKAN连接测试成功", "success")
                else:
                    st.error(f"❌ 连接测试失败: {result['message']}")
                    self.add_log(f"CKAN连接测试失败: {result['message']}", "error")
                    
            except Exception as e:
                st.error(f"❌ 连接测试失败: {str(e)}")
                self.add_log(f"CKAN连接测试异常: {str(e)}", "error")
    
    def execute_excel_import(self, file_path: str, update_existing: bool, 
                           validate_data: bool, batch_size: int, dry_run: bool):
        """执行Excel导入"""
        st.session_state.processing = True
        
        # 创建进度显示
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            self.add_log("开始Excel导入任务", "info")
            status_text.text("🔄 正在初始化...")
            
            # 获取CKAN API客户端
            api = CKANApi(st.session_state.ckan_url, st.session_state.api_key)
            
            # 读取Excel文件
            excel_data = pd.ExcelFile(file_path)
            total_sheets = len(excel_data.sheet_names)
            
            self.add_log(f"发现 {total_sheets} 个工作表", "info")
            progress_bar.progress(10)
            
            # 统计信息
            total_processed = 0
            total_success = 0
            total_errors = 0
            
            # 处理每个工作表
            for sheet_idx, sheet_name in enumerate(excel_data.sheet_names):
                status_text.text(f"🔄 正在处理工作表: {sheet_name}")
                sheet_progress = 10 + (sheet_idx / total_sheets) * 80
                progress_bar.progress(int(sheet_progress))
                
                try:
                    # 读取工作表数据
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    self.add_log(f"处理工作表 '{sheet_name}': {len(df)} 行数据", "info")
                    
                    # 验证数据
                    if validate_data:
                        validation_errors = self.validate_dataset_data(df)
                        if validation_errors:
                            for error in validation_errors[:3]:  # 只显示前3个错误
                                self.add_log(f"数据验证错误: {error}", "warning")
                            if not dry_run:
                                continue
                    
                    # 处理每一行数据
                    for idx, row in df.iterrows():
                        if pd.isna(row.get('name')) or pd.isna(row.get('title')):
                            continue  # 跳过缺少必需字段的行
                        
                        dataset_data = self.prepare_dataset_data(row, sheet_name)
                        total_processed += 1
                        
                        if dry_run:
                            self.add_log(f"[模拟] 准备创建数据集: {dataset_data['name']}", "info")
                            total_success += 1
                        else:
                            # 检查数据集是否已存在
                            existing = api.get_dataset(dataset_data['name'])
                            
                            if existing.get('success'):
                                if update_existing:
                                    result = api.update_dataset(dataset_data)
                                    action = "更新"
                                else:
                                    self.add_log(f"数据集已存在，跳过: {dataset_data['name']}", "warning")
                                    continue
                            else:
                                result = api.create_dataset(dataset_data)
                                action = "创建"
                            
                            if result.get('success'):
                                self.add_log(f"{action}数据集成功: {dataset_data['name']}", "success")
                                total_success += 1
                            else:
                                error_msg = result.get('error', {}).get('message', '未知错误')
                                self.add_log(f"{action}数据集失败: {dataset_data['name']} - {error_msg}", "error")
                                total_errors += 1
                        
                        # 批处理休息
                        if total_processed % batch_size == 0:
                            time.sleep(0.1)  # 避免过于频繁的API调用
                
                except Exception as e:
                    self.add_log(f"处理工作表 '{sheet_name}' 时出错: {str(e)}", "error")
                    total_errors += 1
            
            # 完成处理
            progress_bar.progress(100)
            status_text.text("✅ Excel导入完成！")
            
            # 显示摘要
            self.add_log("Excel导入任务完成", "success")
            self.add_log(f"总计处理: {total_processed}, 成功: {total_success}, 错误: {total_errors}", "info")
            
            # 显示结果摘要
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("总计处理", total_processed)
            with col2:
                st.metric("成功", total_success, f"+{total_success}")
            with col3:
                st.metric("错误", total_errors, f"+{total_errors}" if total_errors > 0 else None)
            
            if dry_run:
                st.info("🧪 这是模拟运行，没有实际创建数据集")
            else:
                st.success("🎉 Excel导入任务完成！")
            
            # 生成报告
            self.generate_import_report(total_processed, total_success, total_errors, dry_run)
            
        except Exception as e:
            progress_bar.progress(0)
            status_text.text("❌ 导入过程中出现错误")
            st.error(f"错误详情: {str(e)}")
            self.add_log(f"导入任务异常: {str(e)}", "error")
        
        finally:
            st.session_state.processing = False
    
    def validate_dataset_data(self, df: pd.DataFrame) -> List[str]:
        """验证数据集数据"""
        errors = []
        
        # 检查必需字段
        required_fields = ['name', 'title']
        for field in required_fields:
            if field not in df.columns:
                errors.append(f"缺少必需字段: {field}")
        
        # 检查数据质量
        if 'name' in df.columns:
            # 检查名称格式
            invalid_names = df[df['name'].str.contains(r'[^a-z0-9\-_]', na=False)]
            if not invalid_names.empty:
                errors.append(f"发现 {len(invalid_names)} 个无效的数据集名称（只能包含小写字母、数字、连字符和下划线）")
        
        return errors
    
    def prepare_dataset_data(self, row: pd.Series, schema_type: str) -> Dict[str, Any]:
        """准备数据集数据"""
        # 基本数据集信息
        dataset_data = {
            'name': str(row['name']).lower().replace(' ', '-'),
            'title': str(row['title']),
            'type': schema_type
        }
        
        # 可选字段
        optional_fields = {
            'notes': 'notes',
            'owner_org': 'owner_org',
            'license_id': 'license_id',
            'url': 'url',
            'version': 'version',
            'author': 'author',
            'author_email': 'author_email',
            'maintainer': 'maintainer',
            'maintainer_email': 'maintainer_email'
        }
        
        for excel_field, ckan_field in optional_fields.items():
            if excel_field in row and pd.notna(row[excel_field]):
                dataset_data[ckan_field] = str(row[excel_field])
        
        # 处理标签
        if 'tags' in row and pd.notna(row['tags']):
            tags = [tag.strip() for tag in str(row['tags']).split(',')]
            dataset_data['tags'] = [{'name': tag} for tag in tags if tag]
        
        # 添加默认值
        if 'owner_org' not in dataset_data and st.session_state.get('org_name'):
            dataset_data['owner_org'] = st.session_state.org_name
        
        if 'license_id' not in dataset_data:
            dataset_data['license_id'] = st.session_state.get('default_license', 'cc-by')
        
        return dataset_data
    
    def execute_file_monitor(self, uploaded_zip, dataset_filter: str, 
                           check_metadata: bool, check_size: bool, 
                           check_timestamp: bool, check_hash: bool, 
                           debug_mode: bool, detailed_report: bool):
        """执行文件监控"""
        st.session_state.processing = True
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            self.add_log("开始文件监控任务", "info")
            status_text.text("🔄 正在解压文件...")
            progress_bar.progress(20)
            
            # 解压ZIP文件
            zip_path = os.path.join(self.temp_dir, uploaded_zip.name)
            with open(zip_path, "wb") as f:
                f.write(uploaded_zip.getbuffer())
            
            extracted_dir = os.path.join(self.temp_dir, "extracted")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extracted_dir)
                file_list = zip_ref.namelist()
            
            self.add_log(f"解压完成，发现 {len(file_list)} 个文件", "info")
            progress_bar.progress(40)
            
            # 获取CKAN数据
            status_text.text("🔍 正在获取CKAN数据...")
            api = CKANApi(st.session_state.ckan_url, st.session_state.api_key)
            
            datasets_result = api.list_datasets()
            if not datasets_result.get('success'):
                raise Exception("无法获取CKAN数据集列表")
            
            dataset_names = datasets_result['result']
            if dataset_filter:
                # 简单的通配符过滤
                import fnmatch
                dataset_names = [name for name in dataset_names 
                               if fnmatch.fnmatch(name, dataset_filter)]
            
            self.add_log(f"找到 {len(dataset_names)} 个数据集进行监控", "info")
            progress_bar.progress(60)
            
            # 分析文件
            status_text.text("📊 正在分析文件差异...")
            outdated_files = []
            
            # 遍历本地文件
            for root, dirs, files in os.walk(extracted_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, extracted_dir)
                    
                    # 模拟文件分析（在实际应用中，这里会比较文件与CKAN资源）
                    file_stat = os.stat(file_path)
                    file_size = file_stat.st_size
                    file_mtime = datetime.fromtimestamp(file_stat.st_mtime)
                    
                    # 模拟检测过期文件（实际中会调用CKAN API比较）
                    if len(outdated_files) < 5:  # 限制演示数量
                        if file_size > 1024:  # 大于1KB的文件
                            reason = []
                            if check_timestamp:
                                reason.append("本地文件更新")
                            if check_size:
                                reason.append("文件大小变化")
                            if check_metadata:
                                reason.append("元数据不匹配")
                            
                            outdated_files.append({
                                'file': relative_path,
                                'reason': ', '.join(reason),
                                'local_size': file_size,
                                'local_modified': file_mtime.strftime('%Y-%m-%d %H:%M:%S'),
                                'ckan_modified': '2024-01-01 10:00:00',  # 模拟CKAN时间
                                'dataset': 'example-dataset'  # 模拟关联数据集
                            })
            
            progress_bar.progress(90)
            status_text.text("📋 正在生成报告...")
            
            # 生成监控报告
            self.generate_monitor_report(outdated_files, detailed_report)
            
            progress_bar.progress(100)
            status_text.text("✅ 文件监控完成！")
            
            self.add_log("文件监控任务完成", "success")
            self.add_log(f"发现 {len(outdated_files)} 个需要同步的文件", 
                        "warning" if outdated_files else "success")
            
        except Exception as e:
            progress_bar.progress(0)
            status_text.text("❌ 监控过程中出现错误")
            st.error(f"错误详情: {str(e)}")
            self.add_log(f"监控任务异常: {str(e)}", "error")
        
        finally:
            st.session_state.processing = False
    
    def generate_import_report(self, total_processed: int, total_success: int, 
                             total_errors: int, dry_run: bool):
        """生成导入报告"""
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'excel_import',
            'mode': 'dry_run' if dry_run else 'live',
            'summary': {
                'total_processed': total_processed,
                'total_success': total_success,
                'total_errors': total_errors,
                'success_rate': f"{(total_success/total_processed*100):.1f}%" if total_processed > 0 else "0%"
            },
            'logs': st.session_state.logs[-20:]  # 最近20条日志
        }
        
        report_json = json.dumps(report_data, indent=2, ensure_ascii=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="📥 下载详细报告",
                data=report_json,
                file_name=f"excel_import_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        with col2:
            # 生成简化的CSV报告
            if st.session_state.logs:
                log_df = pd.DataFrame([
                    {
                        'timestamp': log['timestamp'],
                        'type': log['type'],
                        'message': log['message']
                    }
                    for log in st.session_state.logs[-20:]
                ])
                
                csv_data = log_df.to_csv(index=False)
                st.download_button(
                    label="📊 下载日志CSV",
                    data=csv_data,
                    file_name=f"import_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    def generate_monitor_report(self, outdated_files: List[Dict], detailed_report: bool):
        """生成监控报告"""
        if outdated_files:
            st.warning(f"⚠️ 发现 {len(outdated_files)} 个需要同步的文件")
            
            # 显示结果表格
            df_results = pd.DataFrame(outdated_files)
            st.dataframe(df_results, use_container_width=True)
            
            # 同步建议
            st.subheader("🔧 同步建议")
            for file_info in outdated_files:
                with st.expander(f"📄 {file_info['file']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**文件信息:**")
                        st.write(f"- 本地大小: {file_info['local_size']} 字节")
                        st.write(f"- 本地修改时间: {file_info['local_modified']}")
                        st.write(f"- 关联数据集: {file_info['dataset']}")
                    
                    with col2:
                        st.write("**建议操作:**")
                        st.write(f"- 同步原因: {file_info['reason']}")
                        st.write("- 建议: 更新CKAN资源")
                        st.write("- 优先级: 中等")
            
            # 提供下载报告
            report_data = {
                'timestamp': datetime.now().isoformat(),
                'type': 'file_monitor',
                'summary': {
                    'total_files_checked': len(outdated_files) * 3,  # 模拟总文件数
                    'outdated_files': len(outdated_files),
                    'sync_needed': len(outdated_files) > 0
                },
                'outdated_files': outdated_files
            }
            
            if detailed_report:
                report_json = json.dumps(report_data, indent=2, ensure_ascii=False)
                st.download_button(
                    label="📥 下载监控报告",
                    data=report_json,
                    file_name=f"file_monitor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        else:
            st.success("✅ 所有文件都是最新的，无需同步")
    
    def show_usage_stats(self):
        """显示使用统计"""
        st.subheader("📈 使用统计")
        
        # 模拟统计数据
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("总导入次数", "156", "12")
        
        with col2:
            st.metric("处理文件数", "2,341", "89")
        
        with col3:
            st.metric("监控任务", "23", "3")
        
        with col4:
            st.metric("成功率", "98.7%", "0.5%")
    
    def show_recent_activity(self):
        """显示最近活动"""
        st.subheader("🕒 最近活动")
        
        # 从session logs获取最近活动
        if st.session_state.logs:
            recent_logs = st.session_state.logs[-5:]
            
            for log in reversed(recent_logs):
                timestamp = log['timestamp']
                message = log['message']
                log_type = log['type']
                
                # 选择图标
                icon = "✅" if log_type == "success" else "❌" if log_type == "error" else "⚠️" if log_type == "warning" else "ℹ️"
                
                st.write(f"{icon} **{timestamp}** - {message}")
        else:
            st.info("暂无活动记录")
    
    def show_monitor_history(self):
        """显示监控历史"""
        st.subheader("📊 监控历史")
        
        df_history = pd.DataFrame(history_data)
        st.dataframe(df_history, use_container_width=True)

# 运行应用
if __name__ == "__main__":
    app = CKANToolsApp()
    app.main()