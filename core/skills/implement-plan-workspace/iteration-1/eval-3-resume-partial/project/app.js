const { validateEmail, validateAge } = require('./validator');

function processRegistration(data) {
  try {
    validateEmail(data.email);
  } catch (e) {
    console.error('Validation failed', { field: 'email', error: e.message });
    throw e;
  }

  try {
    validateAge(data.age);
  } catch (e) {
    console.error('Validation failed', { field: 'age', error: e.message });
    throw e;
  }

  const result = {
    email: data.email,
    age: data.age,
    registeredAt: new Date().toISOString(),
  };

  console.info('Registration successful', { email: data.email });

  return result;
}

module.exports = { processRegistration };
