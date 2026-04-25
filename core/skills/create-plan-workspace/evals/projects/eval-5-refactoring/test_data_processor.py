from data_processor import process, get_supported_formats


class TestProcessJSON:
    def test_single_object(self):
        result = process('{"name": "alice", "age": "30"}', "json")
        assert len(result) == 1
        assert result[0]["source"] == "json"
        assert result[0]["fields"]["name"] == "alice"

    def test_array(self):
        result = process('[{"a": 1}, {"b": 2}]', "json")
        assert len(result) == 2

    def test_field_count(self):
        result = process('{"x": 1, "y": 2, "z": 3}', "json")
        assert result[0]["field_count"] == 3


class TestProcessCSV:
    def test_basic(self):
        data = "name,email\nalice,alice@example.com\nbob,bob@example.com"
        result = process(data, "csv")
        assert len(result) == 2
        assert result[0]["fields"]["name"] == "alice"

    def test_strips_whitespace(self):
        data = "name,email\n  alice , alice@example.com "
        result = process(data, "csv")
        assert result[0]["fields"]["name"] == "alice"


class TestProcessKeyValue:
    def test_basic(self):
        data = "host=localhost\nport=5432\ndb=myapp"
        result = process(data, "key_value")
        assert len(result) == 3
        assert result[0]["fields"]["host"] == "localhost"

    def test_skips_invalid_lines(self):
        data = "valid=yes\ninvalid line\nalso_valid=true"
        result = process(data, "key_value")
        assert len(result) == 2


class TestProcessXMLSimple:
    def test_single_record(self):
        data = "<record>\n<name>\nalice\n</name>\n<age>\n30\n</age>\n</record>"
        result = process(data, "xml_simple")
        assert len(result) == 1
        assert result[0]["fields"]["name"] == "alice"
        assert result[0]["fields"]["age"] == "30"


class TestProcessFixedWidth:
    def test_basic(self):
        data = "name      age  city\nalice     30   madrid\nbob       25   london"
        result = process(data, "fixed_width")
        assert len(result) == 2
        assert result[0]["fields"]["name"] == "alice"


class TestSupportedFormats:
    def test_lists_all(self):
        formats = get_supported_formats()
        assert "json" in formats
        assert "csv" in formats
        assert "key_value" in formats
        assert "xml_simple" in formats
        assert "fixed_width" in formats

    def test_unsupported_raises(self):
        try:
            process("data", "yaml")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Unsupported format" in str(e)
