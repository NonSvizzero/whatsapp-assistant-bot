from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import time
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import quote_plus


driver = webdriver.Chrome()                     # Needs to be global for all classes to use
driver.get('https://web.whatsapp.com')


class BotConfig(object):
    last_msg = False
    last_msg_id = False

    command_history = []
    last_command = ""

    def __init__(self, contact_list):
        self.contacts = contact_list

    def get_contacts(self):
        return self.contacts

    def set_last_chat_message(self, msg, time_id):
        self.last_msg = msg
        self.last_msg_id = time_id

    def get_last_chat_message(self):
        return self.last_msg, self.last_msg_id

    def set_last_command(self, command):
        self.last_command = command
        self.command_history.append(command)

    def get_command_history(self):
        return "You have asked the following commands: " + ", ".join(self.command_history)


class Bot(object):
    def __init__(self):
        self.config = BotConfig(contact_list=whatsapp_contacts())
        self.init_bot()

    def init_bot(self):
        while True:
            self.poll_chat()

    @staticmethod
    def _chat_history():
        text_bubbles = driver.find_elements_by_class_name("message-out")
        # message-in = receiver, message-out = sender

        tmp_queue = []

        for bubble in text_bubbles:
            msg_texts = bubble.find_elements_by_class_name("bubble-text")

            for msg in msg_texts:
                raw_msg_text = msg.find_element_by_class_name("emojitext").text.lower()
                # raw_msg_time = msg.find_element_by_class_name("bubble-text-meta").text        # time message sent
                tmp_queue.append(raw_msg_text)

        return tmp_queue[-1]        # Send last message in list

    def poll_chat(self):
        last_msg = self._chat_history()

        time_id = time.strftime('%H-%M-%S', time.gmtime())

        last_saved_msg, last_saved_msg_id = self.config.get_last_chat_message()
        if last_saved_msg != last_msg and last_saved_msg_id != time_id:
            self.config.set_last_chat_message(msg=last_msg, time_id=time_id)

            print(self.config.get_last_chat_message())

            is_action = is_action_message(last_msg=last_msg)
            if is_action:
                self.config.set_last_command(last_msg)
                self.bot_options(action=last_msg)

        else:
            pass

    def bot_options(self, action):
        simple_menu = {                                 # function requires no extra arguments
            "hi": say_hi,
            "help": help_commands,
            "all_commands": self.config.get_command_history,
        }

        try:
            command_args = action[1:].split(" ", 1)
            print(command_args)

            if len(command_args) == 1:
                send_message(simple_menu[command_args[0]]())

            else:
                # Complex bot commands
                if command_args[0] == "google":
                    query = "".join(command_args[1])
                    g_search = GoogleResults(search=True)
                    g_search.search(qry=query)
                    g_search.execute_search()

                elif command_args[0] == "images":
                    query = "".join(command_args[1])
                    g_images = GoogleResults(images=True)
                    g_images.images(qry=query)
                    g_images.execute_search()

                elif command_args[0] == "maps":
                    # TODO - check the correct amount, need to poll user for info
                    # TODO - redo this later
                    map_commands = command_args[1].split(" ")
                    origin = map_commands[0]
                    destination = map_commands[1]
                    mode = map_commands[2]

                    g_maps = GoogleResults(maps=True)
                    g_maps.maps(origin=origin, destination=destination, travel_mode=mode)
                    g_maps.execute_search()

        except KeyError as e:
            print("Key Error Exception: {err}".format(err=str(e)))
            send_message("Wrong command. Send me /help to see a list of valid commands")


class GoogleResults(object):
    search_url = False

    def __init__(self, **kwargs):
        # Normal Search
        self.google_search = kwargs.get('search', False)

        # Image Search
        self.google_images = kwargs.get('images', False)

        # Google Maps Directions
        self.google_maps = kwargs.get('maps', False)

    def search(self, qry):
        send_message("Searching Google for: '{qry}'".format(qry=qry))

        if self.google_search:
            self.search_url = 'https://www.google.com/search?hl=en&q={qry}'.format(qry=qry)

    def images(self, qry):
        send_message("Searching Google Images for: '{qry}'".format(qry=qry))

        if self.google_images:
            self.search_url = 'https://www.google.com/search?hl=en&q={qry}&tbm=isch'.format(qry=qry)

    def maps(self, origin, destination, **kwargs):
        send_message("Searching Google Maps: '{ori} to {dest}'".format(ori=origin, dest=destination))
        # https://developers.google.com/maps/documentation/urls/guide
        # TODO - add streetview and the other maps options

        if self.google_maps:
            t_mode = self._check_travel_mode(kwargs.get('travel_mode', "driving"))     # default to driving

            print(origin, destination, t_mode)
            if origin and destination and t_mode:
                self.search_url = self._build_maps_url(ori=origin, dest=destination, t_mode=t_mode)

    @staticmethod
    def _build_maps_url(ori, dest, t_mode):
        base_url = "https://www.google.com/maps/dir/?api=1&"
        custom_url = base_url + "origin={ori}&destination={dest}&travelmode={t_mode}.".format(
            ori=quote_plus(ori),
            dest=quote_plus(dest),
            t_mode=quote_plus(t_mode)
        )
        print(custom_url)
        return custom_url

    @staticmethod
    def _check_travel_mode(t_mode):
        available_modes = ["driving", "walking", "transit", "biking"]
        if t_mode not in available_modes:
            return False

        return t_mode

    def execute_search(self):
        # TODO - add a delay as kwargs between opening page & screenshot
        if self.search_url:
            driver.execute_script("window.open('','_blank');")
            driver.switch_to.window(driver.window_handles[1])
            driver.get(self.search_url)  # search image
            time.sleep(1.5)
            driver.save_screenshot('screenshot.png')  # take screenshot
            driver.close()  # close window
            driver.switch_to.window(driver.window_handles[0])  # switch back to whatsapp

            self._attach_and_send_screenshot()

        else:
            print("Search URL has not been set, follow the class setup\n")

    @staticmethod
    def _attach_and_send_screenshot():
        try:
            # open attach menu
            attach_btn = driver.find_element_by_xpath('//*[@id="main"]/header/div[3]/div/div[2]/div')
            attach_btn.click()

            # Find attach file btn and send screenshot path to input
            time.sleep(1)
            attach_img_btn = driver.find_element_by_xpath(
                '//*[@id="main"]/header/div[3]/div/div[2]/span/div/div/ul/li[1]/input')  # Had to do xpath on input

            attach_img_btn.send_keys(os.getcwd() + "/screenshot.png")           # get current script path + img_path
            time.sleep(1)
            send_btn = driver.find_element_by_xpath(  # send image
                '//*[@id="app"]/div/div/div[1]/div[2]/span/div/span/div/div/div[2]/span[2]/div/div')
            send_btn.click()

            # close attach menu
            time.sleep(1)
            attach_btn = driver.find_element_by_xpath('//*[@id="main"]/header/div[3]/div/div[2]/div')
            attach_btn.click()

        except NoSuchElementException as e:
            print(str(e))
            send_message("Bot failed to retrieve search content, try again...")


"""
Simple Commands
"""


def help_commands():
    print("Asking for help")
    return "Commands: /hi, /all_commands, /google {query}, /images {query}, /maps {from} {to}"


def say_hi():
    print("Saying hi")
    return "Bot says hi"


"""
Helper Methods
"""


def is_action_message(last_msg):
    if last_msg[0] == "/":
        return True

    time.sleep(0.5)
    return False


def send_message(msg):
    whatsapp_msg = driver.find_element_by_class_name('pluggable-input-body')
    whatsapp_msg.send_keys(msg)
    whatsapp_msg.send_keys(Keys.ENTER)


# Get all the contacts
def whatsapp_contacts():
    contacts = driver.find_elements_by_class_name("chat-title")

    return [contact.text for contact in contacts]


if __name__ == "__main__":
    input("Waiting for QR Code Scan\n")
    Bot()