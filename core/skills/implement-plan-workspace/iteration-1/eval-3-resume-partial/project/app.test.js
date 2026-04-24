const { processRegistration } = require('./app');

describe('processRegistration', () => {
  test('validates email', () => {
    expect(() => processRegistration({ email: 'bad', age: 25 })).toThrow('Invalid email format');
  });

  test('validates age', () => {
    expect(() => processRegistration({ email: 'a@b.com', age: -1 })).toThrow('Age must be between 0 and 150');
  });

  test('succeeds with valid data', () => {
    const result = processRegistration({ email: 'test@example.com', age: 30 });
    expect(result.email).toBe('test@example.com');
    expect(result.age).toBe(30);
    expect(result.registeredAt).toBeDefined();
  });

  test('logs validation errors', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
    try {
      processRegistration({ email: 'bad', age: 25 });
    } catch (e) {
      // expected
    }
    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining('Validation failed'),
      expect.objectContaining({ field: 'email' })
    );
    consoleSpy.mockRestore();
  });

  test('logs successful registration', () => {
    const consoleSpy = jest.spyOn(console, 'info').mockImplementation();
    processRegistration({ email: 'test@example.com', age: 30 });
    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining('Registration successful'),
      expect.objectContaining({ email: 'test@example.com' })
    );
    consoleSpy.mockRestore();
  });
});
