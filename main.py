import base64
import logging
import boto3
import io
import json
import requests
from botocore.exceptions import ClientError
from datetime import datetime
logger = logging.getLogger()
logger.setLevel(logging.INFO)
from selenium import webdriver
from tempfile import mkdtemp
from selenium.webdriver.common.by import By
#from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

def handler(event=None, context=None):  
    logger.info(json.dumps(event))
    # Parse the JSON string in the "body" field
    #body_dict = json.loads(event['body'])
    #url=body_dict['queryStringParameters']['url']
    
    
    publicIp = '0.0.0.0'
    metadata_url = 'http://169.254.169.254/latest/meta-data/public-ipv4'
    try:
        publicIp = requests.get('http://checkip.amazonaws.com').text.rstrip()
    except:
        publicIp = 'Unable to retrieve public IP address.'
    
    url=event['queryStringParameters']['url']
        
    if not check_url_availability(url):
        response= {
        'statusCode': 500,
        'headers': {
	    'Access-Control-Allow-Origin': '*',
	    'Access-Control-Allow-Headers': 'Content-Type',
	    'Access-Control-Allow-Methods': 'OPTIONS,HEAD,POST',
            'Content-Type': 'application/json'	    
        },
        'body': json.dumps({'publicIp': 'not available', 
                            'elapsedTime': '0 second', 
                            'fileSize': '0 KB',
                            'url': ''})
        }    
        return response

    options = webdriver.ChromeOptions()
    #options.add_experimental_option('prefs', {'intl.accept_languages': 'en,en_US'})
    prefs = {
          "translate_whitelists": {"your native language":"en"},
          "translate":{"enabled":"True"}
    }
    options.add_experimental_option("prefs", prefs)
    options.binary_location = '/opt/chrome/chrome'
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-gpu")
    options.add_argument('--disable-extensions')
    options.add_argument('--start-maximized')    
    options.add_argument("--window-size=1280x1696")
    options.add_argument("--single-process")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-dev-tools")
    options.add_argument("--no-zygote")
    options.add_argument(f"--user-data-dir={mkdtemp()}")
    options.add_argument(f"--data-path={mkdtemp()}")
    options.add_argument(f"--disk-cache-dir={mkdtemp()}")
    options.add_argument("--remote-debugging-port=9222")
    
    
    # set page load strategy to eager
    options.page_load_strategy = 'eager'    
    
    chrome = webdriver.Chrome("/opt/chromedriver",
                              options=options)
    

    
    before_time = datetime.now()

    try:
        # Set the page load timeout to 30 seconds
        #chrome.set_page_load_timeout(30)   
        chrome.get(url)
    
        width = chrome.execute_script ("return document.body.offsetWidth")
        height = chrome.execute_script ("return document.body.offsetHeight")
        #wait = WebDriverWait(chrome, 25)
        #width = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body"))).get_attribute("offsetWidth")
        #height = chrome.execute_script ("return document.body.offsetHeight")  
        
        if width < 600:
          width = 600
        
        if height < 800:
          height = 800
        
        chrome.set_window_size(width, height)
    
        #WebDriverWait(chrome, 25).until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR,"iframe#whovaIframeSpeaker")))
        screenshot = chrome.get_screenshot_as_png()
        #chrome.save_screenshot('image.png')
    
        #return chrome.find_element(by=By.XPATH, value="//html").text
    
        #decodescreenshot=base64.b64encode(screenshot).decode('utf-8')
        #logger.info(decodescreenshot)

        region = boto3.Session().region_name
        eurl='https://s3-'+region+'.amazonaws.com'
        s3 = boto3.client('s3', region_name=region,config=boto3.session.Config(s3={'addressing_style': 'virtual'}, signature_version='s3v4'))
        bucketname='geoimagebucket-'+region
        logger.info(region)
        logger.info(eurl)

        after_time = datetime.now()
    
        elapsed_time = (after_time - before_time).total_seconds()
    
        current_time = after_time.strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"screenshot_{current_time}.png"

        byteio = io.BytesIO(screenshot)

        # get the size of the data in bytes
        sizebypeio = byteio.getbuffer().nbytes
    
        # convert the size to a human-readable format
        size_str = human_readable_size(sizebypeio)

  
        s3.upload_fileobj(byteio, bucketname, file_name)
        url1 = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': bucketname,
                'Key': file_name
            },
            ExpiresIn=24 * 3600
        )

                
        response= {
        'statusCode': 200,
        'headers': {
	    'Access-Control-Allow-Origin': '*',
	    'Access-Control-Allow-Headers': 'Content-Type',
	    'Access-Control-Allow-Methods': 'OPTIONS,HEAD,POST',
            'Content-Type': 'application/json'	    
        },
        'body': json.dumps({'publicIp': publicIp, 
                            'elapsedTime': f'{elapsed_time:.3f} seconds', 
                            'fileSize': size_str,
                            'url': url1})
        }
        
        print("Upload Successful", url1)
        return response
        
        #return url1
        #below not used
        #return {
        #'statusCode': 200,
        #'headers': {
        #    'Content-Type': 'image/png',
        #    'Content-Disposition': 'inline; filename="screenshot.png"'
        #},
        #'body': decodescreenshot,
        #'isBase64Encoded': True
        #}
    except ClientError as e:

        response= {
        'statusCode': 500,
        'headers': {
	    'Access-Control-Allow-Origin': '*',
	    'Access-Control-Allow-Headers': 'Content-Type',
	    'Access-Control-Allow-Methods': 'OPTIONS,HEAD,POST',
            'Content-Type': 'application/json'	    
        },
        'body': json.dumps({'publicIp': 'time is out', 
                            'elapsedTime': '0 second', 
                            'fileSize': '0 KB',
                            'url': ''})
        }    
        return response

        logging.error('error3:'+str(e))
        return None

def human_readable_size(size_bytes):
    """Converts a file size in bytes to a human-readable format."""
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(units) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {units[i]}"

def check_url_availability(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True
        else:
            logger.info('error1:'+str(response))
            return True
    except requests.exceptions.RequestException as e:
        logger.info('error2:'+str(e.response))
        return False    
