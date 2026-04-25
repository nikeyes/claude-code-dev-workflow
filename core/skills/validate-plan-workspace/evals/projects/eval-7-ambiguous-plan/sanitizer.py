import html


class DataSanitizer:
    def sanitize_string(self, value):
        if not isinstance(value, str):
            return str(value)
        return value.strip()

    def sanitize_email(self, value):
        email = value.strip().lower()
        if "@" not in email:
            raise ValueError(f"Invalid email: {value}")
        return email

    def sanitize_html(self, value):
        return html.escape(value)

    def sanitize_record(self, record):
        result = {}
        for key, value in record.items():
            if isinstance(value, str):
                if "email" in key.lower():
                    result[key] = self.sanitize_email(value)
                elif "html" in key.lower() or "body" in key.lower():
                    result[key] = self.sanitize_html(value)
                else:
                    result[key] = self.sanitize_string(value)
            else:
                result[key] = value
        return result
