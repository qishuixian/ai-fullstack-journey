# 模拟 API 返回的对话标签列表（有重复）
raw_tags = ["Python", "AI", "Python", "前端", "AI", "转型"]

# 1. 用集合推导式：提取去重后的标签
unique_tags = {tag for tag in raw_tags}
print("去重后的标签:", unique_tags)

# 2. 用字典推导式：给标签建立 ID 映射
tag_map = {tag: idx for idx, tag in enumerate(unique_tags)}
print("标签映射:", tag_map)

# 3. 用列表推导式：筛选出包含 'A' 的标签并转为大写
upper_a_tags = [tag.upper() for tag in raw_tags if 'A' in tag.upper()]
print("包含A的标签:", upper_a_tags)

# 4. 用生成器表达式：模拟逐条处理大量对话历史（省内存）
history_stream = (f"处理第 {i} 条消息..." for i in range(1, 1000000))
print("生成器创建成功，内存占用极小")
print(next(history_stream))  # 输出: 处理第 1 条消息...