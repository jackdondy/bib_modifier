
# BibTeX Modifier

## 项目功能

本项目主要用于修改`.bib`文件，有以下主要功能:

1. **移除未使用的条目并排序**：根据给定 .aux 文件中的引用顺序，移除未使用的条目并排序剩余条目。
2. **期刊名称转换**：根据提供的 [IEEEfull.bib](https://ctan.org/tex-archive/macros/latex/contrib/IEEEtran/bibtex)，将期刊名称替换为其字符串定义。（可用于期刊自动简写）
3. **标题保护**：在引文标题外添加额外的大括号，防止 BibTeX 自动将文本转换为小写。
4. **日期更新**：使用 Everything 搜索工具从本地 PDF 文件中提取出版日期，自动更新引文的 year 和 month 字段。


## 安装指南

### 第 1 步：创建 Conda 环境
我们建议使用 Conda 来管理依赖项。按照以下步骤创建并激活环境：

```bash
conda create -n bib_modifier python=3.12 conda-forge::pypdf2
conda activate bib_modifier
git clone https://github.com/jackdondy/bib_modifier.git
```

### 第 2 步：安装 Everything 命令行界面（可选）

此脚本可使用 Everything 搜索工具来查找 PDF 文件。

1. 下载并安装 [Everything](https://www.voidtools.com/en-us/support/everything/installing_everything/)，并确保其正在运行。
2. 下载 [Everything CLI](https://www.voidtools.com/en-us/support/everything/command_line_interface/)，确保 CLI 可执行文件（es.exe）在系统 PATH 中可访问，或在脚本中指定其路径。


## 使用说明
### 第 1 步：准备输入文件

1. IEEEfull.bib：包含 IEEE 期刊缩写映射的文件[下载链接与使用说明](https://ctan.org/tex-archive/macros/latex/contrib/IEEEtran/bibtex)。
2. .aux 文件：由你的 LaTeX 项目生成。
3. 原始 BibTeX 文件：你想要更新的引用文件。

### 第 2 步：配置路径
根据实际文件位置修改脚本中的文件路径：

```python
ieee_path = r'your/path/IEEEfull.bib'
aux_path = r'your/path/your_project.aux'
bib_path = r'your/path/original.bib'
new_bib_path = r'your/path/updated.bib'
```

设置 `skip_date_check` 为 `False` 如果你希望根据本地 PDF 文件更新引文的 `year` 和 `month` 字段。

```python
# 如果未安装 Everything 或不需要更新日期
# skip_date_check = True 
# 如果已安装 Everything
skip_date_check = False  
```

设置 `es_cmd_path` 为 `None` 将使程序使用系统默认的 Everything CLI 路径。你可以在 Windows 命令行中输入 `es` 来测试默认的 Everything CLI。

```python
es_cmd_path = r'your/path/es.exe'
# es_cmd_path = None         # 使用系统默认的 Everything 路径
```

对于 GUI 版本，只需通过文件浏览器指定文件：

<img width="296" alt="image" src="https://github.com/user-attachments/assets/2444338d-2155-4125-93d7-d2a85f6b1aca" />

点击 `Save Config` 按钮后，程序会在当前文件夹下生成一个 `config.json` 文件，并且在下次运行时会自动加载该 `.json` 文件。  
蓝色标签是可点击的，点击后会自动跳转到对应的 URL。


### 第 3 步：运行脚本
在终端中执行脚本：

```bash
python main_with_date_check.py
```
### 第 3.5 步：日期更新（可选）
如果指定了`skip_date_check=False`，则会调用 Everything 搜索工具来查找 PDF 文件。
在处理 PDF 文件时，如果在系统中找到与引文名称匹配的任何 PDF 文件，程序会输出：
```
-----------------press Enter for first result / input index to select a file / a new path / month and year like '2000 jun' / 'S' to skip / 'SS' to skip all / 'DD' to auto run all:
```
如果未找到任何文件，程序会输出
```
-----------------Input new path / month and year like '2000 jun' / 'S' to skip / 'SS' to skip all / 'DD' to auto run all:
```

根据提示进行输入。`DD` 表示程序将自动处理所有引文，如果没有找到任何内容则跳过该引文，如果有匹配文件则使用第一个匹配项。

程序使用 **PyPDF2.PdfReader** 读取本地 PDF 文件，并在 PDF 文件中搜索类似以下的字符串：

```
VOL. 11, NO. 5, 1 MARCH 2024
VOL. 16, NO. 2, FEBRUARY 2017
date of current version 16 September 2022
date of current version July 16, 2021
```
注意：只搜索 PDF 文件的第一页。

### 第 4 步：输出
脚本将在指定路径（`new_bib_path`）生成更新后的 BibTeX 文件。

## 其他
欢迎参与本项目，或报告任何问题和错误。
