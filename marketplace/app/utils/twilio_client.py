import os
from typing import Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException


class TwilioClient:
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.client = None
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)

    def is_configured(self) -> bool:
        return self.client is not None

    async def search_phone_numbers(
        self,
        area_code: Optional[str] = None,
        contains: Optional[str] = None,
        limit: int = 10,
        country: str = "US",
    ) -> list[dict]:
        """Search for available phone numbers on Twilio."""
        if not self.is_configured():
            raise RuntimeError("Twilio not configured. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN")

        try:
            # Search for local numbers
            numbers = self.client.available_phone_numbers(country).local.list(
                area_code=area_code,
                contains=contains,
                limit=limit,
            )

            results = []
            for num in numbers:
                results.append({
                    "number": num.phone_number,
                    "friendly_name": num.friendly_name,
                    "area_code": num.area_code,
                    "price": num.monthly_price,  # Monthly price in USD
                    "iso_country": num.iso_country,
                    "capabilities": {
                        "voice": num.capabilities.voice,
                        "sms": num.capabilities.sms,
                        "mms": num.capabilities.mms,
                    },
                })
            return results
        except TwilioRestException as e:
            raise RuntimeError(f"Twilio search failed: {e.msg}")

    async def purchase_phone_number(self, phone_number: str) -> dict:
        """Purchase a phone number on Twilio."""
        if not self.is_configured():
            raise RuntimeError("Twilio not configured")

        try:
            # Purchase the number
            purchased = self.client.incoming_phone_numbers.create(
                phone_number=phone_number,
            )
            return {
                "sid": purchased.sid,
                "phone_number": purchased.phone_number,
                "friendly_name": purchased.friendly_name,
                "status": purchased.status,
            }
        except TwilioRestException as e:
            raise RuntimeError(f"Twilio purchase failed: {e.msg}")

    async def release_phone_number(self, phone_number: str) -> bool:
        """Release a phone number on Twilio."""
        if not self.is_configured():
            raise RuntimeError("Twilio not configured")

        try:
            # Find the number by phone_number
            numbers = self.client.incoming_phone_numbers.list(
                phone_number=phone_number,
                limit=1,
            )
            if numbers:
                numbers[0].delete()
                return True
            return False
        except TwilioRestException as e:
            raise RuntimeError(f"Twilio release failed: {e.msg}")

    async def configure_number_webhook(
        self,
        phone_number_sid: str,
        voice_url: Optional[str] = None,
        sms_url: Optional[str] = None,
    ) -> dict:
        """Configure webhooks for a purchased number."""
        if not self.is_configured():
            raise RuntimeError("Twilio not configured")

        try:
            updated = self.client.incoming_phone_numbers(phone_number_sid).update(
                voice_url=voice_url,
                sms_url=sms_url,
            )
            return {
                "sid": updated.sid,
                "voice_url": updated.voice_url,
                "sms_url": updated.sms_url,
            }
        except TwilioRestException as e:
            raise RuntimeError(f"Twilio webhook config failed: {e.msg}")

    async def get_number_details(self, phone_number: str) -> Optional[dict]:
        """Get details of a purchased number."""
        if not self.is_configured():
            raise RuntimeError("Twilio not configured")

        try:
            numbers = self.client.incoming_phone_numbers.list(
                phone_number=phone_number,
                limit=1,
            )
            if numbers:
                num = numbers[0]
                return {
                    "sid": num.sid,
                    "phone_number": num.phone_number,
                    "friendly_name": num.friendly_name,
                    "status": num.status,
                    "voice_url": num.voice_url,
                    "sms_url": num.sms_url,
                    "capabilities": {
                        "voice": num.capabilities.voice,
                        "sms": num.capabilities.sms,
                        "mms": num.capabilities.mms,
                    },
                }
            return None
        except TwilioRestException as e:
            raise RuntimeError(f"Twilio get details failed: {e.msg}")