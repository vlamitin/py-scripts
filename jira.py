from config import config
from selenium.webdriver.common.by import By
import selenium.webdriver.support.expected_conditions as EC
import selenium.webdriver.support.ui as ui

class Jira:
    def __init__(self, browser):
        self.browser = browser

    def login(self, passw):
        self.browser.get(config['JIRA']['baseurl'] + '/login')
        logininput = self.browser.find_element_by_css_selector('#username')
        logininput.send_keys(config['JIRA']['login'])

        continuebtn = self.browser.find_element_by_css_selector('#login-submit')
        continuebtn.click()

        self.wait('#password')

        passinput = self.browser.find_element_by_css_selector('#password')
        passinput.send_keys(passw)

        loginbtn = self.browser.find_element_by_css_selector('#login-submit')
        loginbtn.click()



    def wait(self, css_selector):
        ui.WebDriverWait(self.browser, 2).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_selector)))

def pipeline():
    from getpass import getpass
    passw = getpass()

    from selenium import webdriver
    browser = webdriver.Firefox()

    jira = Jira(browser)
    jira.login(passw)

if __name__ == '__main__':
    pipeline()

