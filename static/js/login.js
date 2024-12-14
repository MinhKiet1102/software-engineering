// Xử lý form đăng ký
document.getElementById("registerForm").addEventListener("submit", function (e) {
    e.preventDefault();
    const username = document.getElementById("username").value;
    const fullname = document.getElementById("fullname").value;
    const email = document.getElementById("email").value;
    const phone = document.getElementById("phone").value;
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirmPassword").value;

    if (password !== confirmPassword) {
        alert("Mật khẩu và Xác nhận mật khẩu không khớp!");
        return;
    }

    fetch('/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, fullname, email, phone, password, confirmPassword })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            // window.location.href = "/login.html";  // Chuyển đến trang đăng nhập
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        alert("Lỗi đăng ký: " + error.message);
    });
});



document.getElementById("loginForm")?.addEventListener("submit", function (e) {
    e.preventDefault();  // Ngừng hành động mặc định của form

    const loginEmail = document.getElementById("loginEmail").value;
    const password = document.getElementById("loginPassword").value;

    // Gửi yêu cầu xác thực đến backend (Flask)
    fetch('/login', {  // Đảm bảo URL đúng
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email: loginEmail, mat_khau: password })
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
        if (data.success) {
            alert(data.message); // Hiển thị thông báo đăng nhập thành công
            window.location.href = data.redirect_url; // Chuyển hướng đến trang của người dùng
        } else {
            alert(data.message); // Hiển thị thông báo lỗi
        }
    })
    .catch(error => {
        alert("Lỗi khi đăng nhập: " + error.message);
    });
});

document.getElementById('forgotForm').addEventListener('submit', async function (event) {
    event.preventDefault(); // Ngăn không cho form reload trang

    const email = document.getElementById('forgotEmail').value;

    try {
        const response = await fetch('/forgot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email: email }), // Gửi email tới server
        });

        const result = await response.json();
        if (result.success) {
            alert('OTP đã được gửi! Kiểm tra email của bạn.');
        } else {
            alert('Lỗi: ' + result.message);
        }
    } catch (error) {
        console.error('Lỗi khi gửi OTP:', error);
    }
});






