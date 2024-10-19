from flask import Flask, render_template, request, send_file, jsonify
from datetime import datetime
from io import BytesIO
from weasyprint import HTML
from PIL import Image, ImageChops
import fitz  # PyMuPDF
import os
from weasyprint import CSS
from weasyprint.text.fonts import FontConfiguration
import string
import requests
from datetime import datetime
import random
from tempfile import NamedTemporaryFile

app = Flask(__name__)


def format_date():
    # 获取当前日期
    current_date = datetime.now()

    # 获取年份、月份和日期
    year = current_date.year
    month = current_date.month
    day = current_date.day

    # 生成yyyy/mm/dd格式的字符串
    return f"{year}/{month:02d}/{day:02d}"


# 调用上传阿里云oss的接口
def call_upload_file2oss_service(img_data, file_name):
    upload_url = 'https://util-transfer-file-2-cdn-wuyi.replit.app/upload'
    # 构建表单数据
    form_data = {
        'access_key_id': 'LTAI5tPSaPtdYouef1NASjdE',
        'access_key_secret': os.environ['access_key_secret'],
        'bucket_name': 'feishu-zdjj-card-bucket',
        'endpoint': 'https://oss-cn-beijing.aliyuncs.com'
    }

    files = {'file': (file_name, img_data, 'image/png')}

    # 发送接口请求
    response = requests.post(upload_url, data=form_data, files=files)

    if response.status_code == 200:
        return response.json()['url']
    else:
        return None


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
    cropped_image = trim_image(image)  # 该函数没问题

    # cropped_image = image
    # 关闭 PDF 文档
    pdf_document.close()
    img_byte_arr = BytesIO()
    cropped_image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    print(f"PDF file size: {len(pdf_bytes)} bytes")
    print(f"Generated image size: {cropped_image.size}")

    # 将字节流作为图片保存到本地
    with open("output_image.png", "wb") as f:
        f.write(img_byte_arr.getvalue())

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
    font_config = FontConfiguration()
    css_file = 'card' + str(kwargs['css_selector']) + '.css'
    css_path = os.path.join(os.path.dirname(__file__), 'static', 'styles',
                            css_file)
    # css = CSS(filename=css_path, font_config=font_config)

    # 创建 CSS 对象
    css = CSS(filename=css_path, font_config=font_config)
    
    # 使用 WeasyPrint 生成 PDF 字节流，并传递 CSS
    pdf_file = HTML(string=rendered_html).write_pdf(stylesheets=[css],
                                                    font_config=font_config)

    # 保存 PDF 文件到本地
    output_pdf_path = os.path.join(os.path.dirname(__file__), 'output', 'generated_card.pdf')
    with open(output_pdf_path, 'wb') as f:
        f.write(pdf_file)

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
    title = data.get('title', '')
    name = data.get('name', '')
    timestamp = data.get('time', None)  # 时间戳可以为空
    source = data.get('source', '')
    zoom = data.get('zoom', 8)  # 缩放比例，默认为 8，1~16
    css_selector = data.get('css_selector', '')  # 选择css样式，默认为空

    # 验证 css_selector 如果有值，必须在 1 到 5 的整数范围内
    if css_selector:
        try:
            css_selector_value = int(css_selector)
            if css_selector_value < 1 or css_selector_value > 5:
                return {"error": "The 'css_selector' field must be an integer between 1 and 5."}, 400
        except ValueError:
            return {"error": "The 'css_selector' field must be a valid integer."}, 400
    # 如果时间戳存在，将其转换为日期格式，否则使用默认时间
    if timestamp:
        date_time = datetime.fromtimestamp((timestamp + 8 * 3600))
        time = date_time.strftime("%B %d, %Y")
        print(time)
    else:
        time = ""

    time_name = datetime.now().strftime("%Y-%m-%d-%H%M")

    # 生成随机的4位ID
    random_id = ''.join(
        random.choices(string.ascii_uppercase + string.digits, k=6))

    # 调用核心函数生成图片
    # 假设 generate_card 函数返回一个字节流
    img_data = generate_card(content,
                             title=title,
                             name=name,
                             time=time,
                             zoom=zoom,
                             source=source,
                             css_selector=css_selector)

    # 创建文件名
    filename = f"{time_name}-{random_id}.png"

    # 返回生成的图片作为响应
    return send_file(img_data,
                     mimetype='image/png',
                     as_attachment=True,
                     download_name=filename)

    # 调用上传服务并获取URL
    src = call_upload_file2oss_service(img_data, filename)

    # 返回生成的图片URL
    if src:
        return jsonify({'src': src})
    else:
        return jsonify({'error': 'Failed to upload image.'}), 500


# # 启动 Flask 服务器
# if __name__ == '__main__':
#     # app.run(debug=True)
#     app.run(host='0.0.0.0', port=8080, debug=True)
