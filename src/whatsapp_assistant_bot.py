from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, \
    ElementNotVisibleException
import time
import os
import glob
import random

driver = webdriver.Chrome()  # Needs to be global for all classes to use
driver.get('https://web.whatsapp.com')


class BotConfig(object):
    last_msg = False
    last_msg_id = False

    command_history = []
    last_command = ""

    def set_last_chat_message(self, msg, time_id):
        self.last_msg = msg
        self.last_msg_id = time_id

    def get_last_chat_message(self):
        return self.last_msg, self.last_msg_id


class Bot(object):
    EMOJIS = {u'\U0001f638', u'\U0001f639', u'\U0001f63a', u'\U0001f63b', u'\U0001f63c', u'\U0001f63d', u'\U0001f63e',
              u'\U0001f63f', u'\U0001f640', u'\U0001f431', u'\U0001f408'}

    def __init__(self):
        self.config = BotConfig()
        self.init_bot()

    def init_bot(self):
        while True:
            self.poll_chat()

    def poll_chat(self):
        last_msg = self.chat_history()

        if last_msg:
            time_id = time.strftime('%H-%M-%S', time.gmtime())

            last_saved_msg, last_saved_msg_id = self.config.get_last_chat_message()
            if last_saved_msg != last_msg and last_saved_msg_id != time_id:
                self.config.set_last_chat_message(msg=last_msg, time_id=time_id)

                print(self.config.get_last_chat_message())

                if last_msg in self.EMOJIS:
                    print("Received a cat emoji. Sending cat pic...")
                    self.send_cat_media()

    def chat_history(self, out=True):
        emojis = driver.find_elements_by_xpath("//*[@class='_3lZNp QkfD1 selectable-text invisible-space copyable-text']")
        tmp_queue = []

        try:
            for emoji in emojis:
                # raw_msg_text = msg.find_element_by_class_name("selectable-text.invisible-space.copyable-text").text.lower()
                # raw_msg_time = msg.find_element_by_class_name("bubble-text-meta").text        # time message sent
                tmp_queue.append(emoji.get_attribute("alt"))

            if len(tmp_queue) > 0:
                return tmp_queue[-1]  # Send last message in list

        except StaleElementReferenceException as e:
            print(str(e))
            # Something went wrong, either keep polling until it comes back or figure out alternative

        return False

    def send_message(self, msg):
        whatsapp_msg = driver.find_element_by_class_name('_2S1VP')
        whatsapp_msg.send_keys(msg)
        whatsapp_msg.send_keys(Keys.ENTER)

    def attach_and_send_gif(self, path):
        # TODO - ElementNotVisibleException - this shouldn't happen but when would it

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
            self.send_message((str(e)))
            self.send_message("Bot failed to retrieve search content, try again...")

    def send_cat_media(self):
        medias = [x for x in os.listdir('./src/pics') if x[-4:] in ('.mp4', '.jpg', '.png')]
        media = os.path.join(os.getcwd(), 'src/pics', random.choice(medias))
        self.attach_and_send_gif(media)

if __name__ == "__main__":
    print("Bot is active, scan your QR code from your phone's WhatsApp")
    Bot()
