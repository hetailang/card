from flask import Flask, render_template, request, send_file
from datetime import datetime
from io import BytesIO
from weasyprint import HTML
from PIL import Image, ImageChops
import fitz  # PyMuPDF
import os
from weasyprint import CSS

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


def pdf_to_cropped_png(pdf_bytes, zoom=8):

    # 使用 BytesIO 读取 PDF 字节流
    pdf_stream = BytesIO(pdf_bytes)
    # 打开 PDF 文件
    pdf_document = fitz.open(stream=pdf_stream, filetype="pdf")
    page = pdf_document[0]
    # 设置页面的缩放比例，提升分辨率
    mat = fitz.Matrix(zoom, zoom)
    # 渲染页面为图片
    pix = page.get_pixmap(matrix=mat)
    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    # 裁剪图片的空白区域
    cropped_image = trim_image(image)
    # 关闭 PDF 文档
    pdf_document.close()
    img_byte_arr = BytesIO()
    cropped_image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr
    # 返回字节流，而不是PIL.Image对象

    # return cropped_image


def generate_card(content, **kwargs):

    # # 生成静态文件的绝对路径
    # css_url = url_for('static', filename='styles/card.css', _external=True)

    # 渲染 card.html 模板
    rendered_html = render_template(
        'card.html',
        content=content,
        title=kwargs['title'],
        name=kwargs['name'],
        time=kwargs['time'],
        source=kwargs['source'],
        # css_url=css_url
    )

    # # 使用 WeasyPrint 生成 PDF
    # pdf_file = HTML(string=rendered_html).write_pdf()

    # 获取静态文件的本地路径
    css_path = os.path.join(os.path.dirname(__file__), 'static', 'styles',
                            'card.css')
    css = CSS(filename=css_path)

    # 使用 WeasyPrint 生成 PDF 字节流，并传递 CSS
    pdf_file = HTML(string=rendered_html).write_pdf(stylesheets=[css])

    img_data = pdf_to_cropped_png(pdf_file, kwargs['zoom'])

    # 返回生成的图片
    return img_data


# 生成图片的 API
@app.route('/generate_card', methods=['POST'])
def generate_card_endpoint():
    # 从请求中获取 JSON 数据
    data = request.get_json()

    # 验证请求数据，只强制要求 'content' 字段存在
    content = data.get('content')
    if not content:
        return {"error": "The 'content' field is required."}, 400

    # 获取其他可选字段，如果不存在则设置默认值
    title = data.get('title', 'Untitled')
    name = data.get('name', 'Anonymous')
    timestamp = data.get('time', None)  # 时间戳可以为空
    source = data.get('source', 'Unknown')
    zoom = data.get('zoom', 8)  # 缩放比例，默认为 8，1~16

    # 如果时间戳存在，将其转换为日期格式，否则使用默认时间
    if timestamp:
        date_time = datetime.fromtimestamp(timestamp)
        time = date_time.strftime("%B %d, %Y")
    else:
        time = "N/A"

    # 调用核心函数生成图片
    img_data = generate_card(content,
                             title=title,
                             name=name,
                             time=time,
                             zoom=zoom,
                             source=source)

    # 返回生成的图片作为响应
    return send_file(img_data, mimetype='image/png')


# 启动 Flask 服务器
if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=8080, debug=True)
