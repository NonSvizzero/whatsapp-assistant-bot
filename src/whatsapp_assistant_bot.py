from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, \
    ElementNotVisibleException
from collections import deque, Counter
from datetime import datetime, timedelta
import time
import os
import random

driver = webdriver.Chrome()  # Needs to be global for all classes to use
driver.get('https://web.whatsapp.com')

QUEUE_LEN = 100
EMOJIS = {u'\U0001f638', u'\U0001f639', u'\U0001f63a', u'\U0001f63b', u'\U0001f63c', u'\U0001f63d', u'\U0001f63e',
          u'\U0001f63f', u'\U0001f640', u'\U0001f431', u'\U0001f408'}
PICS_DIR = os.path.expanduser("~/Pictures/cats")


class BotConfig(object):
    messages = deque(maxlen=QUEUE_LEN)
    start = datetime.now() - timedelta(minutes=1)

    def update_messages(self, messages):
        new_messages = [msg for msg in messages if msg[0] in EMOJIS
                        and datetime.strptime(msg[1][1:msg[1].find(']')],'%H:%M, %m/%d/%Y') > self.start]
        diff = Counter(new_messages) - Counter(self.messages)
        self.messages.extend(diff.elements())
        return sum(diff.values())


class Bot(object):
    def __init__(self):
        self.config = BotConfig()
        self.init_bot()

    def init_bot(self):
        while True:
            self.poll_chat()

    def poll_chat(self):
        messages = self.chat_history()
        if messages:
            for _ in range(self.config.update_messages(messages)):
                print("Received a cat emoji. Sending cat pic...")
                self.send_cat_media()

    def chat_history(self, messages=QUEUE_LEN):
        text_bubbles = driver.find_elements_by_class_name("_3DFk6")
        tmp_queue = []

        try:
            for bubble in text_bubbles:
                try:
                    time_sent = bubble.find_element_by_class_name("copyable-text").get_attribute("data-pre-plain-text")
                    emoji = bubble.find_elements_by_xpath(
                        "//*[@class='_3lZNp QkfD1 selectable-text invisible-space copyable-text']")[0].get_attribute(
                        "alt")
                except IndexError:
                    continue
                tmp_queue.append((emoji, time_sent))

            if len(tmp_queue) > 0:
                return tmp_queue[-min(messages, len(tmp_queue)):]  # Send last messages in list

        except StaleElementReferenceException as e:
            print(str(e))
            # Something went wrong, either keep polling until it comes back or figure out alternative

        return False

    def send_message(self, msg):
        whatsapp_msg = driver.find_element_by_class_name('_2S1VP')
        whatsapp_msg.send_keys(msg)
        whatsapp_msg.send_keys(Keys.ENTER)

    def attach_and_send_gif(self, path):
        # local variables for x_path elements on browser
        attach_xpath = '//*[@id="main"]/header/div[3]/div/div[2]/div'
        send_file_xpath = '//*[@id="app"]/div/div/div[1]/div[2]/span/div/span/div/div/div[2]/span[2]/div/div'
        attach_type_xpath = '//*[@id="main"]/header/div[3]/div/div[2]/span/div/div/ul/li[1]/input'

        try:
            # open attach menu
            attach_btn = driver.find_element_by_xpath(attach_xpath)
            attach_btn.click()

            # Find attach file btn and send screenshot path to input
            time.sleep(1)
            attach_img_btn = driver.find_element_by_xpath(attach_type_xpath)

            # TODO - might need to click on transportation mode if url doesn't work
            attach_img_btn.send_keys(path)
            time.sleep(1)
            send_btn = driver.find_element_by_xpath(send_file_xpath)
            send_btn.click()

            # close attach menu
            time.sleep(1)
            attach_btn = driver.find_element_by_xpath(attach_xpath)
            attach_btn.click()

        except (NoSuchElementException, ElementNotVisibleException) as e:
            print(str(e))

    def send_cat_media(self):
        medias = [x for x in os.listdir(PICS_DIR) if x[-4:] in ('.mp4', '.jpg', '.png')]
        media = os.path.join(PICS_DIR, random.choice(medias))
        self.attach_and_send_gif(media)


if __name__ == "__main__":
    print("Bot is active, scan your QR code from your phone's WhatsApp")
    Bot()
