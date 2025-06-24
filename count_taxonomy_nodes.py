#!/usr/bin/env python3
"""
統計InterPro taxonomy JSON文件中的節點數量
"""

import json
import sys
import os
from pathlib import Path

def count_taxonomy_nodes(json_file_path):
    """
    統計JSON文件中的taxonomy節點數量
    
    Args:
        json_file_path (str): JSON文件路徑
        
    Returns:
        dict: 包含統計信息的字典
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 獲取基本統計信息
        total_count = data.get('count', 0)
        results = data.get('results', [])
        actual_nodes = len(results)
        
        # 統計有children的節點數量
        nodes_with_children = 0
        nodes_without_children = 0
        
        for node in results:
            metadata = node.get('metadata', {})
            children = metadata.get('children', [])
            
            if children:
                nodes_with_children += 1
            else:
                nodes_without_children += 1
        
        # 檢查是否有分頁
        has_next_page = data.get('next') is not None
        has_previous_page = data.get('previous') is not None
        
        return {
            'file_path': json_file_path,
            'total_count_from_api': total_count,
            'actual_nodes_in_file': actual_nodes,
            'nodes_with_children': nodes_with_children,
            'nodes_without_children': nodes_without_children,
            'has_next_page': has_next_page,
            'has_previous_page': has_previous_page,
            'is_complete_dataset': not has_next_page and not has_previous_page
        }
        
    except FileNotFoundError:
        print(f"❌ 文件不存在: {json_file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析錯誤: {e}")
        return None
    except Exception as e:
        print(f"❌ 處理文件時發生錯誤: {e}")
        return None

def print_statistics(stats):
    """
    打印統計結果
    
    Args:
        stats (dict): 統計信息字典
    """
    if not stats:
        return
    
    print("=" * 60)
    print(f"📊 Taxonomy節點統計結果")
    print("=" * 60)
    print(f"📁 文件路徑: {stats['file_path']}")
    print(f"🔢 API返回的總數量: {stats['total_count_from_api']:,}")
    print(f"📋 文件中實際節點數: {stats['actual_nodes_in_file']:,}")
    print(f"🌳 有子節點的節點數: {stats['nodes_with_children']:,}")
    print(f"🍃 葉子節點數: {stats['nodes_without_children']:,}")
    print(f"📄 有下一頁: {'是' if stats['has_next_page'] else '否'}")
    print(f"📄 有上一頁: {'是' if stats['has_previous_page'] else '否'}")
    print(f"✅ 完整數據集: {'是' if stats['is_complete_dataset'] else '否'}")
    
    if not stats['is_complete_dataset']:
        print(f"⚠️  注意: 這不是完整的數據集，總共有 {stats['total_count_from_api']:,} 個節點")
        print(f"   當前文件只包含 {stats['actual_nodes_in_file']:,} 個節點")

def process_directory(directory_path):
    """
    批量處理目錄中的所有JSON文件

    Args:
        directory_path (str): 目錄路徑
    """
    json_files = list(Path(directory_path).glob("*_taxonomy.json"))

    if not json_files:
        print(f"❌ 在目錄 {directory_path} 中沒有找到 *_taxonomy.json 文件")
        return

    print(f"🔍 找到 {len(json_files)} 個taxonomy JSON文件")
    print("=" * 80)

    total_api_count = 0
    total_actual_nodes = 0
    complete_files = 0
    incomplete_files = 0

    for json_file in sorted(json_files):
        stats = count_taxonomy_nodes(str(json_file))
        if stats:
            ipr_id = json_file.stem.replace('_taxonomy', '')
            print(f"📄 {ipr_id}: {stats['actual_nodes_in_file']:,} 節點 "
                  f"(總共 {stats['total_count_from_api']:,})")

            total_api_count += stats['total_count_from_api']
            total_actual_nodes += stats['actual_nodes_in_file']

            if stats['is_complete_dataset']:
                complete_files += 1
            else:
                incomplete_files += 1
        else:
            print(f"❌ 處理失敗: {json_file}")

    print("=" * 80)
    print(f"📊 總結:")
    print(f"   處理的文件數: {len(json_files)}")
    print(f"   完整數據集: {complete_files}")
    print(f"   不完整數據集: {incomplete_files}")
    print(f"   API總節點數: {total_api_count:,}")
    print(f"   實際下載節點數: {total_actual_nodes:,}")

def main():
    """
    主函數
    """
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  單個文件: python count_taxonomy_nodes.py <json_file_path>")
        print("  批量處理: python count_taxonomy_nodes.py <directory_path>")
        print("例如:")
        print("  python count_taxonomy_nodes.py database/interpro_type_domain/IPR000008_taxonomy.json")
        print("  python count_taxonomy_nodes.py database/interpro_type_domain/")
        sys.exit(1)

    input_path = sys.argv[1]

    # 檢查輸入是文件還是目錄
    if os.path.isfile(input_path):
        # 處理單個文件
        stats = count_taxonomy_nodes(input_path)
        if stats:
            print_statistics(stats)
        else:
            print("❌ 統計失敗")
            sys.exit(1)
    elif os.path.isdir(input_path):
        # 批量處理目錄
        process_directory(input_path)
    else:
        print(f"❌ 路徑不存在: {input_path}")
        sys.exit(1)

if __name__ == "__main__":
    main()
