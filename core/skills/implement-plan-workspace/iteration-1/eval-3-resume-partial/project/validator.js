function validateEmail(email) {
  if (!email || typeof email !== 'string') {
    throw new Error('Email is required and must be a string');
  }
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    throw new Error('Invalid email format');
  }
  return true;
}

function validateAge(age) {
  if (age === null || age === undefined) {
    throw new Error('Age is required');
  }
  if (typeof age !== 'number' || !Number.isInteger(age)) {
    throw new Error('Age must be an integer');
  }
  if (age < 0 || age > 150) {
    throw new Error('Age must be between 0 and 150');
  }
  return true;
}

module.exports = { validateEmail, validateAge };
