from config import Base_URL


class login_user:

    def __init__(self, page):

        self.page = page

        self.email = page.locator('//input[@placeholder="example@sansad.nic.in"]')
        page.wait_for_timeout(300)
        page.screenshot(path="D://SDS_Screenshots//Login//Email.png")
        self.send_otp = page.locator("//button[text()=' Send OTP ']")

        self.otp_box_1 = page.locator("(//input[@type='text'])[1]")
        page.wait_for_timeout(100)
        self.otp_box_2 = page.locator("(//input[@type='text'])[2]")
        page.wait_for_timeout(100)
        self.otp_box_3 = page.locator("(//input[@type='text'])[3]")
        page.wait_for_timeout(100)
        self.otp_box_4 = page.locator("(//input[@type='text'])[4]")
        page.wait_for_timeout(100)
        self.otp_box_5 = page.locator("(//input[@type='text'])[5]")
        page.wait_for_timeout(100)
        self.otp_box_6 = page.locator("(//input[@type='text'])[6]")
        page.wait_for_timeout(500)

        page.screenshot(path="D://SDS_Screenshots//Login//OTP.png")

        self.verify_OTP_CTA = page.locator(
            "//button[text()=' Verify OTP ']"
        )


    def login_navigation(self):

        self.email.fill("claim.rev@rajyasabha.digital")

        self.send_otp.click()

        self.otp_box_1.fill("1")
        self.otp_box_2.fill("2")
        self.otp_box_3.fill("3")
        self.otp_box_4.fill("4")
        self.otp_box_5.fill("5")
        self.otp_box_6.fill("6")

        self.verify_OTP_CTA.click()

        title = self.page.title()

        print(title)