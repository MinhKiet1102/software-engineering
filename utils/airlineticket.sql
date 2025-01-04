-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Máy chủ: 127.0.0.1
-- Thời gian đã tạo: Th12 30, 2024 lúc 01:18 PM
-- Phiên bản máy phục vụ: 10.4.32-MariaDB
-- Phiên bản PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Cơ sở dữ liệu: `airlineticket_db5`
--

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `airports`
--

CREATE TABLE `airports` (
  `id` int(11) NOT NULL,
  `abbreviate_name` varchar(10) NOT NULL,
  `name` varchar(100) NOT NULL,
  `location` varchar(100) NOT NULL,
  `nation` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `airports`
--

INSERT INTO `airports` (`id`, `abbreviate_name`, `name`, `location`, `nation`) VALUES
(1, 'SGN', 'Sân bay Tân Sơn Nhất', 'TP.Hồ Chí Minh', 'Việt Nam'),
(2, 'HAN', 'Sân bay Nội Bài', 'Hà Nội', 'Việt Nam'),
(3, 'DAD', 'Sân bay Đà Nẵng', 'Đà Nẵng', 'Việt Nam'),
(4, 'VCA', 'Sân bay Cần Thơ', 'Cần Thơ', 'Việt Nam'),
(5, 'PQC', 'Sân bay Phú Quốc', 'Kiên Giang', 'Việt Nam'),
(6, 'VDO', 'Sân bay Vân Đồn', 'Quảng Ninh', 'Việt Nam'),
(7, 'CXR', 'Sân bay Cam Ranh', 'Khánh Hòa', 'Việt Nam'),
(8, 'VII', 'Sân bay Vinh', 'TP.Hồ Chí Minh', 'Việt Nam'),
(9, 'HUI', 'Sân bay Phú Bài', 'Thừa Thiên Huế', 'Việt Nam'),
(10, 'UIH', 'Sân bay Phù Cát', 'Bình Định', 'Việt Nam'),
(11, 'BMV', 'Sân bay Buôn Ma Thuột', 'Đắk Lắk', 'Việt Nam');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `bookings`
--

CREATE TABLE `bookings` (
  `id` int(11) NOT NULL,
  `fullname` varchar(100) NOT NULL,
  `identity_card` varchar(20) NOT NULL,
  `phone_number` int(11) NOT NULL,
  `booking_date` datetime NOT NULL DEFAULT current_timestamp(),
  `customer_id` int(11) NOT NULL,
  `flight_schedule_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `bookings`
--

INSERT INTO `bookings` (`id`, `fullname`, `identity_card`, `phone_number`, `booking_date`, `customer_id`, `flight_schedule_id`) VALUES
(12, 'Nguyễn Thanh Nở', '0123456789', 123456798, '2024-12-27 15:04:23', 2, 1),
(13, 'Lê Minh Kiệt', '0123456789', 123456798, '2024-12-27 15:05:56', 2, 1),
(14, 'Võ Trần Yến Như', '0123456789', 123456798, '2024-12-27 15:54:19', 2, 1),
(15, 'Nguyễn Thanh Nở', '0123456789', 123456798, '2024-12-27 15:58:12', 2, 1),
(17, 'Nguyễn Thanh Nở', '0123456789', 123456798, '2024-12-27 16:35:06', 3, 1),
(18, 'Lê Minh Kiệt', '0123456789', 123456798, '2024-12-27 16:39:15', 3, 1),
(19, 'Trần Thị D', '0123456789', 123456798, '2024-12-27 17:10:07', 2, 1),
(20, 'Hữu Hậu', '0123456789', 123456798, '2024-12-27 17:12:40', 3, 1),
(21, 'Nguyễn Thanh Nở', '0123456789', 123456798, '2024-12-27 17:35:23', 2, 1),
(22, 'Lê Minh Kiệt', '0123456789', 123456798, '2024-12-27 18:26:35', 2, 1),
(23, 'Võ Trần Yến Như', '0123456789', 123456798, '2024-12-27 18:43:46', 3, 1),
(24, 'Nguyễn Thanh Nở', '0123456789', 123456798, '2024-12-28 13:17:54', 4, 3),
(25, 'Nguyễn Thanh Nở', '0123456789', 123456798, '2024-12-28 13:26:58', 4, 3),
(26, 'Nguyễn Thanh Nở', '0123456789', 123456798, '2024-12-29 16:04:20', 2, 1),
(27, 'Nguyễn Thanh Nở', '0123456789', 123456798, '2024-12-29 16:08:50', 3, 2),
(28, 'Lê Minh Kiệt', '0123456789', 123456798, '2024-12-30 11:25:12', 2, 2),
(29, 'Võ Trần Yến Như', '0123456789', 123456798, '2024-12-30 14:00:34', 2, 3),
(30, 'Nguyễn Thanh Nở', '0123456789', 123456798, '2024-12-30 14:14:25', 3, 2),
(31, 'Nguyễn Thanh Nở', '0123456789', 123456798, '2024-12-30 14:21:14', 3, 3),
(32, 'Nguyễn Thanh Nở', '0123456789', 123456798, '2024-12-30 14:53:27', 2, 2),
(33, 'Nguyễn Thanh Nở', '0123456789', 123456798, '2024-12-30 14:54:44', 3, 2),
(34, 'Nguyễn Thanh Nở', '0123456789', 123456798, '2024-12-30 15:07:58', 2, 2),
(35, 'Võ Trần Yến Như', '0123456789', 123456798, '2024-12-30 19:12:26', 2, 3);

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `booking_tickets`
--

CREATE TABLE `booking_tickets` (
  `id` int(11) NOT NULL,
  `booking_id` int(11) NOT NULL,
  `ticket_id` int(11) NOT NULL,
  `quantity` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `booking_tickets`
--

INSERT INTO `booking_tickets` (`id`, `booking_id`, `ticket_id`, `quantity`) VALUES
(12, 12, 9, 3),
(13, 13, 10, 3),
(14, 14, 9, 2),
(15, 15, 10, 3),
(17, 17, 9, 2),
(18, 18, 9, 2),
(19, 19, 10, 2),
(20, 20, 9, 2),
(21, 21, 10, 2),
(22, 22, 10, 3),
(23, 23, 9, 3),
(24, 24, 3, 7),
(25, 25, 2, 2),
(26, 26, 9, 1),
(27, 27, 1, 2),
(28, 28, 1, 2),
(29, 29, 3, 2),
(30, 30, 1, 2),
(31, 31, 3, 2),
(32, 32, 1, 2),
(33, 33, 1, 2),
(34, 34, 1, 2),
(35, 35, 3, 2);

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `flights`
--

CREATE TABLE `flights` (
  `id` varchar(10) NOT NULL,
  `start_location` varchar(100) NOT NULL,
  `destination` varchar(100) NOT NULL,
  `start_location_id` varchar(10) DEFAULT NULL,
  `destination_id` varchar(10) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `flights`
--

INSERT INTO `flights` (`id`, `start_location`, `destination`, `start_location_id`, `destination_id`) VALUES
('VN1200', 'TP.Hồ Chí Minh', 'Hà Nội', 'SGN', 'HAN'),
('VN1201', 'Hà Nội', 'Đà Nẵng', 'HAN', 'DAD'),
('VN1202', 'Đà Nẵng', 'Kiên Giang', 'DAD', 'PQC'),
('VN1203', 'TP.Hồ Chí Minh', 'Cần Thơ', 'SGN', 'VCA'),
('VN1204', 'Hà Nội', 'Kiên Giang', 'HAN', 'PQC'),
('VN1205', 'TP.Hồ Chí Minh', 'Đắk Lắk', 'SGN', 'BMV');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `flight_schedules`
--

CREATE TABLE `flight_schedules` (
  `id` int(11) NOT NULL,
  `start_date` datetime NOT NULL,
  `flight_id` varchar(10) NOT NULL,
  `flight_time` float NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `flight_schedules`
--

INSERT INTO `flight_schedules` (`id`, `start_date`, `flight_id`, `flight_time`) VALUES
(1, '2025-01-01 08:00:00', 'VN1200', 120),
(2, '2025-01-02 10:30:00', 'VN1201', 90),
(3, '2025-01-03 15:45:00', 'VN1202', 60),
(4, '2025-01-04 12:15:00', 'VN1203', 75),
(5, '2025-01-05 09:20:00', 'VN1204', 120),
(6, '2024-12-29 18:48:00', 'VN1205', 90),
(7, '2024-12-29 19:56:00', 'VN1200', 90);

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `intermediate_airports`
--

CREATE TABLE `intermediate_airports` (
  `id` int(11) NOT NULL,
  `note` varchar(255) DEFAULT NULL,
  `stop_time` int(11) NOT NULL,
  `airport_id` varchar(10) NOT NULL,
  `flight_schedule_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `payments`
--

CREATE TABLE `payments` (
  `id` int(11) NOT NULL,
  `amount` float NOT NULL,
  `payment_method` varchar(50) NOT NULL,
  `payment_date` datetime NOT NULL,
  `booking_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `payments`
--

INSERT INTO `payments` (`id`, `amount`, `payment_method`, `payment_date`, `booking_id`) VALUES
(12, 4500000, 'VNPay', '2024-12-27 08:04:23', 12),
(13, 2550000, 'VNPay', '2024-12-27 08:05:56', 13),
(14, 3300000, 'VNPay', '2024-12-27 08:54:19', 14),
(15, 2850000, 'VNPay', '2024-12-27 08:58:12', 15),
(18, 3300000, 'Tại quầy', '2024-12-27 09:39:15', 18),
(19, 1900000, 'VNPay', '2024-12-27 10:10:07', 19),
(20, 3300000, 'Tại quầy', '2024-12-27 10:12:40', 20),
(21, 1900000, 'VNPay', '2024-12-27 10:35:23', 21),
(22, 2850000, 'VNPay', '2024-12-27 11:26:35', 22),
(23, 4950000, 'Tại quầy', '2024-12-27 11:43:46', 23),
(24, 5600000, 'VNPay', '2024-12-28 06:17:54', 24),
(25, 2900000, 'VNPay', '2024-12-28 06:26:58', 25),
(26, 1650000, 'VNPay', '2024-12-29 09:04:20', 26),
(27, 2700000, 'Tại quầy', '2024-12-29 09:08:50', 27),
(28, 2700000, 'VNPay', '2024-12-30 04:25:12', 28),
(29, 1600000, 'VNPay', '2024-12-30 07:00:34', 29),
(30, 2700000, 'Tại quầy', '2024-12-30 07:14:25', 30),
(31, 1600000, 'Tại quầy', '2024-12-30 07:21:14', 31),
(32, 2700000, 'VNPay', '2024-12-30 07:53:27', 32),
(33, 2700000, 'Tại quầy', '2024-12-30 07:54:44', 33),
(34, 2700000, 'VNPay', '2024-12-30 08:07:58', 34),
(35, 1600000, 'VNPay', '2024-12-30 12:12:26', 35);

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `rules`
--

CREATE TABLE `rules` (
  `id` int(11) NOT NULL,
  `quantity_airport` int(11) NOT NULL,
  `min_flight_time` int(11) NOT NULL,
  `max_intermediate_airport` int(11) NOT NULL,
  `min_stop_time` int(11) NOT NULL,
  `max_stop_time` int(11) NOT NULL,
  `time_buy` int(11) NOT NULL,
  `time_sell` int(11) NOT NULL,
  `admin_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `rules`
--

INSERT INTO `rules` (`id`, `quantity_airport`, `min_flight_time`, `max_intermediate_airport`, `min_stop_time`, `max_stop_time`, `time_buy`, `time_sell`, `admin_id`) VALUES
(1, 20, 60, 2, 15, 30, 12, 4, 1);

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `seats`
--

CREATE TABLE `seats` (
  `id` int(11) NOT NULL,
  `seat_number` varchar(10) NOT NULL,
  `ticket_id` int(11) NOT NULL,
  `status` varchar(10) NOT NULL,
  `booking_ticket_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `seats`
--

INSERT INTO `seats` (`id`, `seat_number`, `ticket_id`, `status`, `booking_ticket_id`) VALUES
(27, '1', 9, 'booked', 12),
(28, '2', 9, 'booked', 12),
(29, '7', 9, 'booked', 12),
(30, '1', 10, 'booked', 13),
(31, '10', 10, 'booked', 13),
(32, '13', 10, 'booked', 13),
(33, '4', 9, 'booked', 14),
(34, '8', 9, 'booked', 14),
(35, '2', 10, 'booked', 15),
(36, '6', 10, 'booked', 15),
(37, '8', 10, 'booked', 15),
(38, '5', 9, 'booked', 17),
(39, '10', 9, 'booked', 17),
(40, '11', 9, 'booked', 18),
(41, '12', 9, 'booked', 18),
(42, '7', 10, 'booked', 19),
(43, '11', 10, 'booked', 19),
(44, '13', 9, 'booked', 20),
(45, '15', 9, 'booked', 20),
(46, '4', 10, 'booked', 21),
(47, '3', 10, 'booked', 21),
(48, '5', 10, 'booked', 22),
(49, '9', 10, 'booked', 22),
(50, '12', 10, 'booked', 22),
(51, '3', 9, 'booked', 23),
(52, '6', 9, 'booked', 23),
(53, '9', 9, 'booked', 23),
(54, '1', 3, 'booked', 24),
(55, '10', 3, 'booked', 24),
(56, '13', 3, 'booked', 24),
(57, '16', 3, 'booked', 24),
(58, '11', 3, 'booked', 24),
(59, '15', 3, 'booked', 24),
(60, '8', 3, 'booked', 24),
(61, '1', 2, 'booked', 25),
(62, '11', 2, 'booked', 25),
(63, '14', 9, 'booked', 26),
(64, '8', 1, 'booked', 27),
(65, '10', 1, 'booked', 27),
(66, '12', 1, 'booked', 28),
(67, '14', 1, 'booked', 28),
(68, '4', 3, 'booked', 29),
(69, '6', 3, 'booked', 29),
(70, '4', 1, 'booked', 30),
(71, '3', 1, 'booked', 30),
(72, '7', 3, 'booked', 31),
(73, '9', 3, 'booked', 31),
(74, '2', 1, 'booked', 32),
(75, '1', 1, 'booked', 32),
(76, '7', 1, 'booked', 33),
(77, '6', 1, 'booked', 33),
(78, '11', 1, 'booked', 34),
(79, '15', 1, 'booked', 34),
(80, '12', 3, 'booked', 35),
(81, '18', 3, 'booked', 35);

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `tickets`
--

CREATE TABLE `tickets` (
  `id` int(11) NOT NULL,
  `ticket_class` varchar(50) NOT NULL,
  `price` int(11) NOT NULL,
  `flight_schedule_id` int(11) NOT NULL,
  `quantity` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `tickets`
--

INSERT INTO `tickets` (`id`, `ticket_class`, `price`, `flight_schedule_id`, `quantity`) VALUES
(1, '1', 1200000, 2, 20),
(2, '1', 1300000, 3, 30),
(3, '2', 700000, 3, 30),
(4, '1', 1400000, 4, 40),
(5, '2', 750000, 4, 40),
(6, '1', 1500000, 5, 15),
(7, '2', 1600000, 5, 13),
(8, '2', 4250000, 6, 13),
(9, '1', 1500000, 1, 15),
(10, '2', 850000, 1, 13),
(11, '1', 1500000, 7, 30),
(12, '2', 800000, 2, 24);

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('Customer','Admin','Staff') NOT NULL,
  `fullname` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `phone_number` varchar(15) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `users`
--

INSERT INTO `users` (`id`, `username`, `password`, `role`, `fullname`, `email`, `phone_number`) VALUES
(1, 'thanhno', '202cb962ac59075b964b07152d234b70', 'Admin', 'Nguyễn Thanh Nở', 'no0308@gmail.com', '0123456798'),
(2, 'yennhu', '202cb962ac59075b964b07152d234b70', 'Customer', 'Võ Trần Yến Như', 'yennhu@gmail.com', '0123456798'),
(3, 'minhkiet', '202cb962ac59075b964b07152d234b70', 'Staff', 'Lê Minh Kiệt', 'minhkiet@gmail.com', '0123456798'),
(4, 'nguyenthanhno', '202cb962ac59075b964b07152d234b70', 'Customer', 'Nguyễn Thanh Nở', 'thanhno0308@gmail.com', '0123456798'),
(6, 'minhhuy', '202cb962ac59075b964b07152d234b70', 'Staff', 'Dương Ngọc Minh Huy', 'minhhuy@gmail.com', '0123456798'),
(7, 'ngocquy', '202cb962ac59075b964b07152d234b70', 'Admin', 'Đào Ngọc Quý', 'ngocquy@gmail.com', '0123456798');

--
-- Chỉ mục cho các bảng đã đổ
--

--
-- Chỉ mục cho bảng `airports`
--
ALTER TABLE `airports`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `abbreviate_name` (`abbreviate_name`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Chỉ mục cho bảng `bookings`
--
ALTER TABLE `bookings`
  ADD PRIMARY KEY (`id`),
  ADD KEY `customer_id` (`customer_id`),
  ADD KEY `flight_schedule_id` (`flight_schedule_id`);

--
-- Chỉ mục cho bảng `booking_tickets`
--
ALTER TABLE `booking_tickets`
  ADD PRIMARY KEY (`id`),
  ADD KEY `booking_id` (`booking_id`),
  ADD KEY `ticket_id` (`ticket_id`);

--
-- Chỉ mục cho bảng `flights`
--
ALTER TABLE `flights`
  ADD PRIMARY KEY (`id`),
  ADD KEY `start_location_id` (`start_location_id`),
  ADD KEY `destination_id` (`destination_id`);

--
-- Chỉ mục cho bảng `flight_schedules`
--
ALTER TABLE `flight_schedules`
  ADD PRIMARY KEY (`id`),
  ADD KEY `flight_id` (`flight_id`);

--
-- Chỉ mục cho bảng `intermediate_airports`
--
ALTER TABLE `intermediate_airports`
  ADD PRIMARY KEY (`id`),
  ADD KEY `airport_id` (`airport_id`),
  ADD KEY `flight_schedule_id` (`flight_schedule_id`);

--
-- Chỉ mục cho bảng `payments`
--
ALTER TABLE `payments`
  ADD PRIMARY KEY (`id`),
  ADD KEY `booking_id` (`booking_id`);

--
-- Chỉ mục cho bảng `rules`
--
ALTER TABLE `rules`
  ADD PRIMARY KEY (`id`),
  ADD KEY `admin_id` (`admin_id`);

--
-- Chỉ mục cho bảng `seats`
--
ALTER TABLE `seats`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ticket_id` (`ticket_id`),
  ADD KEY `booking_ticket_id` (`booking_ticket_id`);

--
-- Chỉ mục cho bảng `tickets`
--
ALTER TABLE `tickets`
  ADD PRIMARY KEY (`id`),
  ADD KEY `flight_schedule_id` (`flight_schedule_id`);

--
-- Chỉ mục cho bảng `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT cho các bảng đã đổ
--

--
-- AUTO_INCREMENT cho bảng `airports`
--
ALTER TABLE `airports`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT cho bảng `bookings`
--
ALTER TABLE `bookings`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=36;

--
-- AUTO_INCREMENT cho bảng `booking_tickets`
--
ALTER TABLE `booking_tickets`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=36;

--
-- AUTO_INCREMENT cho bảng `flight_schedules`
--
ALTER TABLE `flight_schedules`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT cho bảng `intermediate_airports`
--
ALTER TABLE `intermediate_airports`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT cho bảng `payments`
--
ALTER TABLE `payments`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=36;

--
-- AUTO_INCREMENT cho bảng `rules`
--
ALTER TABLE `rules`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT cho bảng `seats`
--
ALTER TABLE `seats`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=82;

--
-- AUTO_INCREMENT cho bảng `tickets`
--
ALTER TABLE `tickets`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- AUTO_INCREMENT cho bảng `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- Các ràng buộc cho các bảng đã đổ
--

--
-- Các ràng buộc cho bảng `bookings`
--
ALTER TABLE `bookings`
  ADD CONSTRAINT `bookings_ibfk_1` FOREIGN KEY (`customer_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `bookings_ibfk_2` FOREIGN KEY (`flight_schedule_id`) REFERENCES `flight_schedules` (`id`);

--
-- Các ràng buộc cho bảng `booking_tickets`
--
ALTER TABLE `booking_tickets`
  ADD CONSTRAINT `booking_tickets_ibfk_1` FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`id`),
  ADD CONSTRAINT `booking_tickets_ibfk_2` FOREIGN KEY (`ticket_id`) REFERENCES `tickets` (`id`);

--
-- Các ràng buộc cho bảng `flights`
--
ALTER TABLE `flights`
  ADD CONSTRAINT `flights_ibfk_1` FOREIGN KEY (`start_location_id`) REFERENCES `airports` (`abbreviate_name`),
  ADD CONSTRAINT `flights_ibfk_2` FOREIGN KEY (`destination_id`) REFERENCES `airports` (`abbreviate_name`);

--
-- Các ràng buộc cho bảng `flight_schedules`
--
ALTER TABLE `flight_schedules`
  ADD CONSTRAINT `flight_schedules_ibfk_1` FOREIGN KEY (`flight_id`) REFERENCES `flights` (`id`) ON DELETE CASCADE;

--
-- Các ràng buộc cho bảng `intermediate_airports`
--
ALTER TABLE `intermediate_airports`
  ADD CONSTRAINT `intermediate_airports_ibfk_1` FOREIGN KEY (`airport_id`) REFERENCES `airports` (`abbreviate_name`) ON DELETE CASCADE,
  ADD CONSTRAINT `intermediate_airports_ibfk_2` FOREIGN KEY (`flight_schedule_id`) REFERENCES `flight_schedules` (`id`) ON DELETE CASCADE;

--
-- Các ràng buộc cho bảng `payments`
--
ALTER TABLE `payments`
  ADD CONSTRAINT `payments_ibfk_1` FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`id`);

--
-- Các ràng buộc cho bảng `rules`
--
ALTER TABLE `rules`
  ADD CONSTRAINT `rules_ibfk_1` FOREIGN KEY (`admin_id`) REFERENCES `users` (`id`);

--
-- Các ràng buộc cho bảng `seats`
--
ALTER TABLE `seats`
  ADD CONSTRAINT `seats_ibfk_1` FOREIGN KEY (`ticket_id`) REFERENCES `tickets` (`id`),
  ADD CONSTRAINT `seats_ibfk_2` FOREIGN KEY (`booking_ticket_id`) REFERENCES `booking_tickets` (`id`);

--
-- Các ràng buộc cho bảng `tickets`
--
ALTER TABLE `tickets`
  ADD CONSTRAINT `tickets_ibfk_1` FOREIGN KEY (`flight_schedule_id`) REFERENCES `flight_schedules` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
