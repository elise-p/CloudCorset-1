document.getElementById('signupForm').addEventListener('submit', function (e) {
    e.preventDefault();

    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const city = document.getElementById('city').value;

    if (!name || !email || !city) {
        document.getElementById('responseMessage').textContent = "Please fill in all fields.";
        return;
    }

    const payload = {
        user_email: email,
        user_name: name,
        user_city: city
    };

    fetch('aws-endpoint/addNewUser', { // intentionally redact specific endpoint
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('responseMessage').textContent = "Thanks for signing up! You'll get your outfit suggestions daily around 6AM - 7AM.";
        document.getElementById('signupForm').reset();
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('responseMessage').textContent = "Something went wrong. Please try again.";
    });
});
