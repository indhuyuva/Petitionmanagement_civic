-- phpMyAdmin SQL Dump
-- version 2.11.6
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Feb 27, 2026 at 07:01 AM
-- Server version: 5.0.51
-- PHP Version: 5.2.6

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `civic_complaint`
--

-- --------------------------------------------------------

--
-- Table structure for table `admin`
--

CREATE TABLE `admin` (
  `admin_id` varchar(30) default NULL,
  `email` varchar(40) default NULL,
  `password` varchar(40) default NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `admin`
--

INSERT INTO `admin` (`admin_id`, `email`, `password`) VALUES
('admin', 'admin@gmail.com', 'admin');

-- --------------------------------------------------------

--
-- Table structure for table `citizen_register`
--

CREATE TABLE `citizen_register` (
  `id` int(11) NOT NULL default '0',
  `username` varchar(40) NOT NULL,
  `full_name` varchar(100) default NULL,
  `aadhar` varchar(12) default NULL,
  `mobile` varchar(10) default NULL,
  `email` varchar(100) default NULL,
  `address` varchar(255) default NULL,
  `area` varchar(100) default NULL,
  `city` varchar(100) default NULL,
  `pincode` varchar(6) default NULL,
  `password` varchar(255) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `citizen_register`
--

INSERT INTO `citizen_register` (`id`, `username`, `full_name`, `aadhar`, `mobile`, `email`, `address`, `area`, `city`, `pincode`, `password`) VALUES
(1, 'charles', 'Charles', '824805260323', '8248052603', 'charles@gmail.com', '1342,weststreet', 'Chatiram', 'Trichy', '345678', '123456'),
(2, 'balaji', 'balaji', '678787876789', '8248052603', 'charles@gmail.com', '1342,weststreet', 'Chatiram', 'Trichy', '345678', '123456');

-- --------------------------------------------------------

--
-- Table structure for table `complaints`
--

CREATE TABLE `complaints` (
  `id` int(11) NOT NULL auto_increment,
  `citizen_id` int(11) NOT NULL,
  `case_id` varchar(100) default NULL,
  `assigned_to` int(11) NOT NULL,
  `category` varchar(100) NOT NULL,
  `department` varchar(100) NOT NULL,
  `description` text,
  `area` varchar(150) NOT NULL,
  `ward` varchar(50) NOT NULL,
  `city` varchar(100) NOT NULL,
  `priority` enum('Low','Medium','High','Emergency') NOT NULL,
  `image` varchar(255) NOT NULL,
  `video` varchar(255) default NULL,
  `status` int(11) default '0',
  `created_at` timestamp NOT NULL default CURRENT_TIMESTAMP,
  `updated_at` datetime default NULL,
  `ai_verified` tinyint(4) default '0',
  `ai_reject_reason` varchar(255) default NULL,
  `ai_predicted_label` varchar(50) default NULL,
  `ai_confidence` float default NULL,
  `inspection_notes` text,
  `work_status` enum('Pending','In Progress','Resolved') default 'Pending',
  `resolution_image` varchar(255) default NULL,
  `remarks` text,
  PRIMARY KEY  (`id`),
  KEY `citizen_id` (`citizen_id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=7 ;

--
-- Dumping data for table `complaints`
--

INSERT INTO `complaints` (`id`, `citizen_id`, `case_id`, `assigned_to`, `category`, `department`, `description`, `area`, `ward`, `city`, `priority`, `image`, `video`, `status`, `created_at`, `updated_at`, `ai_verified`, `ai_reject_reason`, `ai_predicted_label`, `ai_confidence`, `inspection_notes`, `work_status`, `resolution_image`, `remarks`) VALUES
(1, 2, 'CC0S6QI', 0, 'Road Damage', 'Public Works', 'Large potholes have formed near Ashok Nagar 2nd Street after recent rains.\r\nThis is causing traffic congestion and accidents during night time.', 'Ashok nagar', '45', 'Tamil Nadu', 'High', '2_1771825295.77677_road_image.jpg', '2_1771825295.777603_road_video.mp4', -1, '2026-02-23 11:11:35', NULL, 0, 'Image does not match selected category', NULL, 0, NULL, 'Pending', NULL, NULL),
(2, 2, 'CC5EBPK', 0, 'Drainage', 'Water Board', 'Overflow water near kknagar', 'Ashok nagar', '45', 'Tamil Nadu', 'Medium', '2_1771930330.324937_download_1.jpg', NULL, -1, '2026-02-24 16:22:10', NULL, 0, 'Image does not match selected category', 'other', 0.5, NULL, 'Pending', NULL, NULL),
(3, 2, 'CC034R5', 0, 'Road Damage', 'Public Works', 'Large potholes have formed on Main Street near Ashok Nagar', 'Chatiram', '45', 'Tamil Nadu', 'High', '2_1771933592.366448_images_4.jpg', NULL, -1, '2026-02-24 17:16:32', NULL, 0, 'Image does not match selected category', 'other', 0.5, NULL, 'Pending', NULL, NULL),
(4, 2, 'CCO8GMW', 0, 'drainage', 'Water Board', 'Overflow water is blocking the drain near KKNagar.', 'Chatiram', '67', 'Tamil Nadu', 'High', '2_1771934183.834516_garbage_1.jpg', NULL, -1, '2026-02-24 17:26:23', NULL, 0, 'Invalid category selected', NULL, 0, NULL, 'Pending', NULL, NULL),
(5, 2, 'CCT6QEE', 10, 'Water Supply', 'Water Board', 'watertank issue', 'chennai', '12', 'Tamil Nadu', 'Medium', '2_1771936148.646566_water_tank.jpg', NULL, 1, '2026-02-24 17:59:08', '2026-02-27 12:04:29', 1, NULL, 'water_tank', 0.95, NULL, 'Resolved', NULL, NULL),
(6, 2, 'CCBIBJ3', 10, 'Road Damage', 'Public Works', 'Road is very damage', 'Trichy', '34', 'Tamil Nadu', 'Medium', '2_1771936460.862542_road_2.jpg', NULL, 2, '2026-02-24 18:04:20', '2026-02-27 11:01:22', 1, NULL, 'road', 0.95, 'completed the pending works', 'Resolved', 'Road2.jpg', 'xxxxxxxxxx');

-- --------------------------------------------------------

--
-- Table structure for table `departments`
--

CREATE TABLE `departments` (
  `dept_id` int(11) NOT NULL auto_increment,
  `dept_name` varchar(100) default NULL,
  `created_at` timestamp NOT NULL default CURRENT_TIMESTAMP,
  PRIMARY KEY  (`dept_id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=3 ;

--
-- Dumping data for table `departments`
--

INSERT INTO `departments` (`dept_id`, `dept_name`, `created_at`) VALUES
(2, 'Roads & Infrastructure', '2026-02-23 19:02:38');

-- --------------------------------------------------------

--
-- Table structure for table `staff_users`
--

CREATE TABLE `staff_users` (
  `staff_id` int(11) NOT NULL auto_increment,
  `name` varchar(100) NOT NULL,
  `email` varchar(100) default NULL,
  `phone` varchar(15) default NULL,
  `role` enum('Department Head','Municipal Officer','Chief Officer') NOT NULL,
  `dept_id` int(11) default NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `status` enum('Active','Inactive') default 'Active',
  `created_at` timestamp NOT NULL default CURRENT_TIMESTAMP,
  PRIMARY KEY  (`staff_id`),
  UNIQUE KEY `username` (`username`),
  KEY `dept_id` (`dept_id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=12 ;

--
-- Dumping data for table `staff_users`
--

INSERT INTO `staff_users` (`staff_id`, `name`, `email`, `phone`, `role`, `dept_id`, `username`, `password`, `status`, `created_at`) VALUES
(5, 'balaji', 'balaji@gmail.com', '8248052603', 'Department Head', 2, 'balaji', '1234', 'Active', '2026-02-23 19:28:36'),
(10, 'vinoth', 'vinoth@gmail.com', '6758765679', 'Municipal Officer', 2, 'vinoth', '1234', 'Active', '2026-02-23 19:56:04'),
(11, 'sanjay', 'sanjay123@gmail.com', '6756765678', 'Chief Officer', 2, 'sanjay', '1234', 'Active', '2026-02-23 21:07:47');

--
-- Constraints for dumped tables
--

--
-- Constraints for table `complaints`
--
ALTER TABLE `complaints`
  ADD CONSTRAINT `complaints_ibfk_1` FOREIGN KEY (`citizen_id`) REFERENCES `citizen_register` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `staff_users`
--
ALTER TABLE `staff_users`
  ADD CONSTRAINT `staff_users_ibfk_1` FOREIGN KEY (`dept_id`) REFERENCES `departments` (`dept_id`) ON DELETE SET NULL;
