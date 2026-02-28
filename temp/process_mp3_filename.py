import os

def modify_mp3_filenames(directory, number_to_add):
    """
    修改指定目录中所有 MP3 文件的文件名。
    将文件名最后两位数字加上指定的数值。

    :param directory: str, 文件所在目录
    :param number_to_add: int, 要加上的数字
    """
    # 确保目录存在
    if not os.path.exists(directory):
        print(f"目录 {directory} 不存在！")
        return

    # 遍历目录中的所有文件
    for filename in os.listdir(directory):
        if filename.endswith('.mp3'):  # 仅处理 MP3 文件
            name, ext = os.path.splitext(filename)  # 分离文件名和扩展名

            # 查找最后的两位数字并修改
            try:
                base_name, last_number = name[:-2], name[-2:]
                new_number = int(last_number) + number_to_add
                new_filename = f"{base_name}{new_number:02d}{ext}"  # 保证两位数字格式

                # 重命名文件
                old_path = os.path.join(directory, filename)
                new_path = os.path.join(directory, new_filename)
                os.rename(old_path, new_path)

                print(f"已重命名: {filename} -> {new_filename}")
            except ValueError:
                # 如果最后两位不是数字，跳过
                print(f"文件 {filename} 不符合规则，跳过处理。")

# 示例调用
modify_mp3_filenames('./mp3_files', 53)
