from config import Base_URL

class IT_Claim_Submission:

    def __init__(self,page):

        self.page = page

        self.IT_Claim_CARD = page.locator('//h3[text()="IT Equipment Claims"]')

        self.add_claim_CTA = page.locator('(//button[@class="underline  px-4 py-2 text-sm flex items-center hover:opacity-90"])[1]')

        self.search_member_CTA = page.locator('//input[@placeholder="Search by Name or IC number..."]')

        #here we will type user name : Deepanshu Hooda and select user and user redirect to claim form 
        