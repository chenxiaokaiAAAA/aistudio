#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF文档解析脚本
用于分析冲印系统传片接口协议说明
"""

import PyPDF2
import sys
import os

def extract_pdf_text(pdf_path):
    """提取PDF文本内容"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            
            print(f"PDF页数: {len(pdf_reader.pages)}")
            print("=" * 50)
            
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                text += page_text
                print(f"第 {page_num + 1} 页内容:")
                print(page_text)
                print("-" * 30)
            
            return text
    except Exception as e:
        print(f"读取PDF失败: {e}")
        return None

def analyze_api_fields(text):
    """分析API字段要求"""
    print("\n=== API字段分析 ===")
    
    # 查找关键字段
    keywords = [
        'product_id', '产品编号', '产品ID', 'product',
        'size', '尺寸', '规格',
        'width', 'height', '宽度', '高度',
        'dpi', '分辨率',
        'file_url', '图片地址', '文件地址',
        'order_id', '订单号', '订单ID',
        'customer', '客户', '收件人',
        'shipping', '配送', '地址'
    ]
    
    for keyword in keywords:
        if keyword in text.lower():
            print(f"发现关键词: {keyword}")
    
    # 查找必填字段标识
    required_indicators = ['必须', '必填', 'required', 'mandatory', '*']
    for indicator in required_indicators:
        if indicator in text:
            print(f"发现必填标识: {indicator}")

def main():
    """主函数"""
    pdf_path = "冲印系统传片接口协议说明(简版)V2.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"PDF文件不存在: {pdf_path}")
        return
    
    print("开始解析PDF文档...")
    text = extract_pdf_text(pdf_path)
    
    if text:
        print("\n=== 完整文本内容 ===")
        print(text)
        
        # 分析API字段
        analyze_api_fields(text)
        
        # 保存到文件
        with open("pdf_content.txt", "w", encoding="utf-8") as f:
            f.write(text)
        print("\n文本内容已保存到 pdf_content.txt")
    else:
        print("PDF解析失败")

if __name__ == '__main__':
    main()

