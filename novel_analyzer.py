
"""
小说角色分析工具 - 模块化完整版
"""

import argparse
import json
import logging
import re
import requests
import sys
import time
import traceback
from typing import List, Dict, Any, Optional, TextIO

class NovelAnalyzer:
    """小说角色分析器（模块化设计）"""
    
    def __init__(self, model_name: str = "qwen3:4b"):
        # 初始化配置
        self.model_name = model_name
        self.api_url = "http://localhost:11434/api/chat"
        self.headers = {
            "Content-Type": "application/json",
            "Accept-Charset": "utf-8"
        }
        self.request_timeout = 3600  # 1小时超时
        self.max_retries = 3
        self.retry_delay = 30
        self.max_text_length = 5000
        
        # 初始化日志系统
        self._setup_logging()

    def _setup_logging(self):
        """配置UTF-8日志系统"""
        self.logger = logging.getLogger('NovelAnalyzer')
        self.logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # 文件处理器(UTF-8)
        file_handler = logging.FileHandler(
            'novel_analysis.log', 
            mode='w', 
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
        # 错误日志重定向
        sys.stderr = open('error.log', 'w', encoding='utf-8')

    def _log_error(self, error: Exception, context: str = ""):
        """记录错误及堆栈跟踪"""
        self.logger.error(f"{context} Error: {str(error)}")
        with open('error.log', 'a', encoding='utf-8') as f:
            f.write(f"\n\n--- Error at {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            f.write(f"Context: {context}\n")
            f.write("".join(traceback.format_exception(type(error), error, error.__traceback__)))
            f.write("\n" + "-"*80 + "\n")

    def read_novel_file(self, file_path: str) -> Optional[str]:
        """
        读取小说文本文件（UTF-8编码）
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容字符串或None(失败时)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.logger.info(f"成功读取文件: {file_path}")
            return content
        except Exception as e:
            self._log_error(e, f"读取文件失败: {file_path}")
            return None

    def split_into_chapters(self, content: str) -> List[Dict[str, str]]:
        """
        分割小说章节（支持'第51章 万药联盟的诞生'格式）
        
        Args:
            content: 小说文本内容
            
        Returns:
            章节列表，每个章节包含title和content
        """
        try:
            # 匹配"第X章 标题"格式
            pattern = re.compile(r'(第[0-9零一二三四五六七八九十百千万]+章\s[^\n]+)\n')
            matches = list(pattern.finditer(content))
            
            if not matches:
                self.logger.warning("未检测到章节标题，将全文作为单章处理")
                return [{"title": "全文", "content": content}]
            
            chapters = []
            for i, match in enumerate(matches):
                title = match.group(1).strip()
                end_pos = matches[i+1].start() if i < len(matches)-1 else len(content)
                chapters.append({
                    "title": title,
                    "content": content[match.end():end_pos].strip()
                })
            
            self.logger.info(f"分割完成，共 {len(chapters)} 个章节")
            for chap in chapters:
                self.logger.info(f"章节: {chap['title']}")
                
            return chapters
        except Exception as e:
            self._log_error(e, "章节分割失败")
            return []

    def _call_model_api(self, prompt: str) -> Optional[Dict]:
        """
        调用qwen3:4b模型API（带重试机制）
        
        Args:
            prompt: 输入提示
            
        Returns:
            API响应数据或None(失败时)
        """
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"调用模型API (尝试 {attempt+1}/{self.max_retries})")
                
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json={
                        "model": self.model_name,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False,
                        "format": "json"
                    },
                    timeout=self.request_timeout
                )
                
                # 记录调试信息
                with open('api_debug.log', 'a', encoding='utf-8') as f:
                    f.write(f"\n\n=== 请求 ===\n{prompt[:200]}...\n")
                    f.write(f"=== 响应 {response.status_code} ===\n{response.text[:1000]}\n")
                
                if response.status_code != 200:
                    self.logger.error(f"API错误状态码: {response.status_code}")
                    continue
                
                # 安全解析JSON
                try:
                    data = response.json()
                    if not isinstance(data, dict):
                        self.logger.error("API返回了非字典格式数据")
                        continue
                        
                    if 'message' not in data or 'content' not in data['message']:
                        self.logger.error("响应缺少必要字段")
                        continue
                        
                    return data
                except json.JSONDecodeError as je:
                    self.logger.error(f"JSON解析失败: {str(je)}")
                    continue
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"请求超时 (尝试 {attempt+1})")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                continue
            except Exception as e:
                self._log_error(e, "API请求异常")
                break
                
        return None

    def extract_character_info(self, text: str) -> Optional[List[Dict]]:
        """
        从文本提取角色信息
        
        Args:
            text: 要分析的文本
            
        Returns:
            角色信息列表或None(失败时)
        """
        prompt = f"""请从以下小说内容提取角色信息，严格按JSON格式返回：
{{
    "characters": [
        {{
            "name": "角色全名",
            "appearance": "外貌特征",
            "personality": "性格特点",
            "relationships": "人物关系",
            "first_appearance": "首次出现场景",
            "significance": "角色重要性"
        }}
    ]
}}

内容要求：
1. 必须使用简体中文
2. 性格特点需详细描述
3. 人物关系需说明与其他角色的互动

小说内容：
{text[:self.max_text_length]}"""
        
        response = self._call_model_api(prompt)
        if not response:
            return None
            
        try:
            content = response['message']['content']
            data = json.loads(content)
            if isinstance(data, dict) and 'characters' in data:
                return data['characters']
        except Exception as e:
            self._log_error(e, "解析角色信息失败")
            
        return None

    def merge_character_data(self, characters_list: List[List[Dict]]) -> Dict[str, Dict]:
        """
        合并去重角色信息
        
        Args:
            characters_list: 多章节的角色信息列表
            
        Returns:
            合并后的角色字典（按角色名索引）
        """
        merged = {}
        
        for characters in characters_list:
            for char in characters:
                name = char.get('name')
                if not name:
                    continue
                    
                if name not in merged:
                    merged[name] = {
                        **char,
                        'appearances': 1,
                        'chapters': [char.get('first_appearance', '')]
                    }
                else:
                    merged[name]['appearances'] += 1
                    merged[name]['chapters'].append(char.get('first_appearance', ''))
                    
                    # 合并各字段（保留最详细的信息）
                    for field in ['appearance', 'personality', 'relationships', 'significance']:
                        if field in char and char[field] and (
                            field not in merged[name] or 
                            len(char[field]) > len(merged[name].get(field, ''))
                        ):
                            merged[name][field] = char[field]
                            
        return merged

    def generate_final_report(self, chapters: List, characters: Dict, failed: int) -> str:
        """
        生成最终分析报告
        
        Args:
            chapters: 章节列表
            characters: 合并后的角色字典
            failed: 失败章节数
            
        Returns:
            格式化报告字符串
        """
        report = f"""=== 小说角色分析报告 ===

【统计信息】
总章节数: {len(chapters)}
成功分析: {len(chapters) - failed}
失败章节: {failed}
发现角色: {len(characters)}

【角色详细信息】
"""
        for name, data in characters.items():
            report += f"""
■ 角色名称: {name}
    ▸ 出现次数: {data.get('appearances', 1)}
    ▸ 出现章节: {', '.join(data.get('chapters', []))}
    ▸ 外貌特征: {data.get('appearance', '无记录')}
    ▸ 性格特点: {data.get('personality', '无记录')}
    ▸ 人物关系: {data.get('relationships', '无记录')}
    ▸ 角色重要性: {data.get('significance', '无记录')}
"""
            report += "━" * 60 + "\n"
            
        return report

    def check_service_available(self) -> bool:
        """检查Ollama服务是否可用"""
        try:
            response = requests.get(
                "http://localhost:11434/api/version",
                timeout=10
            )
            if response.status_code == 200:
                return True
            self.logger.error(f"服务返回错误状态码: {response.status_code}")
            return False
        except Exception as e:
            self._log_error(e, "服务检查失败")
            return False

    def process_novel(self, input_path: str, output_path: str):
        """
        处理整本小说的完整流程
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
        """
        # 第一步：检查服务
        if not self.check_service_available():
            self.logger.error("Ollama服务不可用，请先启动服务")
            return

        # 第二步：读取文件
        self.logger.info("开始处理小说文件...")
        content = self.read_novel_file(input_path)
        if not content:
            return

        # 第三步：分割章节
        chapters = self.split_into_chapters(content)
        if not chapters:
            self.logger.error("无法分割章节，处理终止")
            return

        # 第四步：提取角色信息
        self.logger.info("开始分析各章节角色...")
        all_characters = []
        failed_chapters = 0
        
        for chapter in chapters:
            self.logger.info(f"正在处理: {chapter['title']}")
            characters = self.extract_character_info(chapter['content'])
            
            if characters:
                all_characters.append(characters)
            else:
                failed_chapters += 1
                self.logger.warning(f"章节分析失败: {chapter['title']}")

        # 第五步：合并角色信息
        self.logger.info("合并角色信息...")
        merged_characters = self.merge_character_data(all_characters)

        # 第六步：生成报告
        report = self.generate_final_report(chapters, merged_characters, failed_chapters)
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            self.logger.info(f"分析报告已保存: {output_path}")
        except Exception as e:
            self._log_error(e, "写入报告文件失败")

def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="小说角色分析工具")
    parser.add_argument("-i", "--input", required=True, help="输入小说文件路径")
    parser.add_argument("-o", "--output", default="character_report.txt", help="输出报告文件路径")
    parser.add_argument("-m", "--model", default="qwen3:4b", help="使用的模型名称")
    
    args = parser.parse_args()
    
    analyzer = NovelAnalyzer(args.model)
    analyzer.process_novel(args.input, args.output)

if __name__ == "__main__":
    main()