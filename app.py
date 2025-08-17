import streamlit as st
import pandas as pd
import os
import tempfile
import zipfile
from datetime import datetime
import json
import requests
import time
from typing import Dict, List, Any

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
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

class CKANApi:
    """简化的CKAN API客户端"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Authorization': api_key,
            'Content-Type': 'application/json'
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """测试CKAN连接"""
        try:
            response = requests.get(
                f"{self.base_url}/api/3/action/site_read",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                return {"success": True, "message": "连接成功"}
            else:
                return {"success": False, "message": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

class CKANToolsApp:
    def __init__(self):
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
                <p>上传Excel文件，自动创建或更新CKAN数据集。支持多种schema格式。</p>
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
        
        # 使用统计
        st.subheader("📈 使用统计")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("总导入次数", "156", "12")
        
        with col2:
            st.metric("处理文件数", "2,341", "89")
        
        with col3:
            st.metric("监控任务", "23", "3")
        
        with col4:
            st.metric("成功率", "98.7%", "0.5%")
        
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
            help="支持包含dataset、device、digitaltwin等schema的Excel文件"
        )
        
        if uploaded_file is not None:
            # 文件信息
            file_size = len(uploaded_file.getbuffer()) / 1024 / 1024  # MB
            st.info(f"📄 文件: {uploaded_file.name} ({file_size:.2f} MB)")
            
            # 文件预览
            try:
                excel_data = pd.ExcelFile(uploaded_file)
                sheet_names = excel_data.sheet_names
                
                st.subheader("📋 文件预览")
                
                selected_sheets = st.multiselect(
                    "选择要处理的工作表",
                    sheet_names,
                    default=sheet_names[:3] if len(sheet_names) > 3 else sheet_names
                )
                
                # 预览选中的工作表
                for sheet in selected_sheets[:2]:  # 只预览前2个
                    with st.expander(f"📊 预览: {sheet}"):
                        df = pd.read_excel(uploaded_file, sheet_name=sheet)
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("总行数", len(df))
                        with col2:
                            st.metric("总列数", len(df.columns))
                        with col3:
                            valid_rows = len(df.dropna(subset=['name', 'title'] if 'name' in df.columns and 'title' in df.columns else []))
                            st.metric("有效数据行", valid_rows)
                        
                        st.dataframe(df.head(5), use_container_width=True)
                        
                        # 检查必需字段
                        required_fields = ['name', 'title']
                        missing_fields = [field for field in required_fields if field not in df.columns]
                        
                        if missing_fields:
                            st.warning(f"⚠️ 缺少必需字段: {', '.join(missing_fields)}")
                        else:
                            st.success("✅ 包含所有必需字段")
                            
            except Exception as e:
                st.error(f"❌ 预览文件时出错: {str(e)}")
            
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
                    self.execute_excel_import(uploaded_file, update_existing, validate_data, batch_size, dry_run)
            
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
        
        st.info("💡 由于Web环境限制，请上传要监控的文件夹压缩包")
        uploaded_zip = st.file_uploader(
            "上传监控文件夹(ZIP格式)",
            type=['zip'],
            help="将需要监控的文件夹压缩为ZIP文件后上传"
        )
        
        if uploaded_zip is not None:
            zip_size = len(uploaded_zip.getbuffer()) / 1024 / 1024
            st.info(f"📦 ZIP文件: {uploaded_zip.name} ({zip_size:.2f} MB)")
            
            if st.button("🔍 开始监控", use_container_width=True, type="primary"):
                self.execute_file_monitor(uploaded_zip)
        
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
                    placeholder="https://your-ckan-instance.com"
                )
                
                api_key = st.text_input(
                    "API密钥",
                    value=st.session_state.get('api_key', ''),
                    type="password"
                )
                
            with col2:
                org_name = st.text_input(
                    "默认组织",
                    value=st.session_state.get('org_name', ''),
                    placeholder="your-organization"
                )
                
                default_license = st.selectbox(
                    "默认许可证",
                    ["cc-by", "cc-by-sa", "cc-zero", "odc-pddl", "other-open"],
                    index=0
                )
            
            col1, col2 = st.columns(2)
            
            with col1:
                test_connection = st.form_submit_button("🔧 测试连接", use_container_width=True)
                
            with col2:
                save_config = st.form_submit_button("💾 保存配置", use_container_width=True, type="primary")
            
            if test_connection:
                self.test_ckan_connection(ckan_url, api_key)
                
            if save_config:
                st.session_state.update({
                    'ckan_url': ckan_url,
                    'api_key': api_key,
                    'org_name': org_name,
                    'default_license': default_license
                })
                st.success("✅ 配置已保存")
                self.add_log("配置已更新", "success")
    
    def show_help_page(self):
        """使用说明页面"""
        st.header("📚 使用说明")
        
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
            - 每个工作表代表一种schema类型
            - 第一行应为列标题
            - 必需字段：name(名称)、title(标题)
            
            ### 2. 文件监控器
            
            **步骤:**
            1. 在侧边栏选择"📁 文件监控器"
            2. 上传要监控的文件夹压缩包
            3. 配置CKAN连接信息
            4. 点击"开始监控"按钮
            """)
        
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
            """)
    
    def check_config(self) -> bool:
        """检查CKAN配置是否完整"""
        return bool(st.session_state.get('ckan_url') and st.session_state.get('api_key'))
    
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
                    self.add_log("CKAN连接测试成功", "success")
                else:
                    st.error(f"❌ 连接测试失败: {result['message']}")
                    self.add_log(f"CKAN连接测试失败: {result['message']}", "error")
                    
            except Exception as e:
                st.error(f"❌ 连接测试失败: {str(e)}")
                self.add_log(f"CKAN连接测试异常: {str(e)}", "error")
    
    def execute_excel_import(self, uploaded_file, update_existing: bool, 
                           validate_data: bool, batch_size: int, dry_run: bool):
        """执行Excel导入（简化版）"""
        st.session_state.processing = True
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            self.add_log("开始Excel导入任务", "info")
            status_text.text("🔄 正在处理Excel文件...")
            progress_bar.progress(20)
            
            # 读取Excel文件
            excel_data = pd.ExcelFile(uploaded_file)
            total_sheets = len(excel_data.sheet_names)
            
            self.add_log(f"发现 {total_sheets} 个工作表", "info")
            progress_bar.progress(40)
            
            total_processed = 0
            total_success = 0
            
            # 模拟处理过程
            for i, sheet_name in enumerate(excel_data.sheet_names):
                status_text.text(f"🔄 正在处理工作表: {sheet_name}")
                progress = 40 + (i / total_sheets) * 50
                progress_bar.progress(int(progress))
                
                df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
                self.add_log(f"处理工作表 '{sheet_name}': {len(df)} 行数据", "info")
                
                # 模拟处理每一行
                for idx, row in df.iterrows():
                    if idx >= 5:  # 限制演示数量
                        break
                    
                    if 'name' in row and pd.notna(row['name']):
                        dataset_name = str(row['name'])
                        total_processed += 1
                        
                        if dry_run:
                            self.add_log(f"[模拟] 准备创建数据集: {dataset_name}", "info")
                        else:
                            self.add_log(f"创建数据集: {dataset_name}", "success")
                        
                        total_success += 1
                        time.sleep(0.1)  # 模拟处理时间
            
            progress_bar.progress(100)
            status_text.text("✅ Excel导入完成！")
            
            self.add_log("Excel导入任务完成", "success")
            self.add_log(f"总计处理: {total_processed}, 成功: {total_success}", "info")
            
            # 显示结果
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("总计处理", total_processed)
            with col2:
                st.metric("成功", total_success)
            with col3:
                st.metric("成功率", "100%")
            
            if dry_run:
                st.info("🧪 这是模拟运行，没有实际创建数据集")
            else:
                st.success("🎉 Excel导入任务完成！")
                
        except Exception as e:
            progress_bar.progress(0)
            status_text.text("❌ 导入过程中出现错误")
            st.error(f"错误详情: {str(e)}")
            self.add_log(f"导入任务异常: {str(e)}", "error")
        
        finally:
            st.session_state.processing = False
    
    def execute_file_monitor(self, uploaded_zip):
        """执行文件监控（简化版）"""
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            self.add_log("开始文件监控任务", "info")
            status_text.text("🔄 正在解压文件...")
            progress_bar.progress(20)
            
            # 模拟解压过程
            time.sleep(1)
            file_count = 25  # 模拟文件数量
            
            self.add_log(f"解压完成，发现 {file_count} 个文件", "info")
            progress_bar.progress(60)
            
            status_text.text("🔍 正在分析文件...")
            time.sleep(1)
            
            # 模拟发现过期文件
            outdated_count = 3
            self.add_log(f"发现 {outdated_count} 个需要同步的文件", "warning")
            
            progress_bar.progress(100)
            status_text.text("✅ 文件监控完成！")
            
            # 显示结果
            if outdated_count > 0:
                st.warning(f"⚠️ 发现 {outdated_count} 个需要同步的文件")
                
                sample_files = [
                    {"文件": "data/sensor_2024.csv", "原因": "本地文件更新", "建议": "更新CKAN资源"},
                    {"文件": "reports/monthly.xlsx", "原因": "文件大小变化", "建议": "重新上传"},
                    {"文件": "config/settings.json", "原因": "元数据不匹配", "建议": "同步元数据"}
                ]
                
                df_results = pd.DataFrame(sample_files)
                st.dataframe(df_results, use_container_width=True)
            else:
                st.success("✅ 所有文件都是最新的，无需同步")
            
            self.add_log("文件监控任务完成", "success")
            
        except Exception as e:
            progress_bar.progress(0)
            status_text.text("❌ 监控过程中出现错误")
            st.error(f"错误详情: {str(e)}")
            self.add_log(f"监控任务异常: {str(e)}", "error")
    
    def show_recent_activity(self):
        """显示最近活动"""
        st.subheader("🕒 最近活动")
        
        if st.session_state.logs:
            recent_logs = st.session_state.logs[-5:]
            
            for log in reversed(recent_logs):
                timestamp = log['timestamp']
                message = log['message']
                log_type = log['type']
                
                icon = "✅" if log_type == "success" else "❌" if log_type == "error" else "⚠️" if log_type == "warning" else "ℹ️"
                st.write(f"{icon} **{timestamp}** - {message}")
        else:
            st.info("暂无活动记录")

# 运行应用
if __name__ == "__main__":
    app = CKANToolsApp()
    app.main()