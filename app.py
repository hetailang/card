from flask import Flask, render_template
from flask import url_for
from datetime import datetime
from io import BytesIO
from weasyprint import HTML
from PIL import Image, ImageChops
import fitz  # PyMuPDF


app = Flask(__name__)

# card界面
@app.route('/card.html')
def show_card():
    return render_template('card.html')

# 定义一个根路由，显示 "Hello World"
@app.route('/')
def hello_world():
    return 'Hello, World!'


def trim_image(image):
    """去除图片的空白边界"""
    bg = Image.new(image.mode, image.size, image.getpixel((0, 0)))
    diff = ImageChops.difference(image, bg)
    bbox = diff.getbbox()
    if bbox:
        return image.crop(bbox)
    return image


def pdf_to_cropped_png(pdf_bytes):

    # 使用 BytesIO 读取 PDF 字节流
    pdf_stream = BytesIO(pdf_bytes)
    # 打开 PDF 文件
    pdf_document = fitz.open(stream=pdf_stream, filetype="pdf")
    page = pdf_document[0]
    # 设置页面的缩放比例，提升分辨率
    zoom = 2  # 2 表示放大两倍
    mat = fitz.Matrix(zoom, zoom)
    # 渲染页面为图片
    pix = page.get_pixmap(matrix=mat)
    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    # 裁剪图片的空白区域
    cropped_image = trim_image(image)
    # 关闭 PDF 文档
    pdf_document.close()

    return cropped_image

def generate_card(content, **kwargs):

    # 生成静态文件的绝对路径
    css_url = url_for('static', filename='styles/card.css', _external=True)

    # 渲染 card.html 模板
    rendered_html = render_template(
        'card.html',
        content=content,
        title=kwargs['title'],
        name=kwargs['name'],
        time=kwargs['time'],
        source=kwargs['source'],
        css_url=css_url
    )

    # 使用 WeasyPrint 生成 PDF
    pdf_file = HTML(string=rendered_html).write_pdf()

    img_data = pdf_to_cropped_png(pdf_file)

    # 返回生成的图片
    return img_data

# 定义一个路由来测试生成图片
@app.route('/generate_card_test')
def generate_card_test():

    # 你可以在这里设置要传入的字段内容
    content = "This is the card content"
    title = "Sample Title"
    name = "John Doe"
    timestamp = 1700000000
    source = "Internet"

    date_time = datetime.fromtimestamp(timestamp)
    time = date_time.strftime("%B %d, %Y")
    img_data = generate_card(content, title=title, name=name, time=time, source=source)
    
    # 在本地直接打开图片
    img_data.show()

    return '请查看生成图片'

# 启动 Flask 服务器
if __name__ == '__main__':
    app.run(debug=True)
