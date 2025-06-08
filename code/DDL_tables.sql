-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1:3306
-- Tiempo de generación: 06-06-2025 a las 00:35:13
-- Versión del servidor: 10.11.10-MariaDB
-- Versión de PHP: 7.2.34

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `u143586701_Proyecto_final`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `businesses`
--

CREATE TABLE `businesses` (
  `business_id` int(11) NOT NULL,
  `business_name` varchar(255) NOT NULL,
  `county_id` int(11) DEFAULT NULL,
  `Address` text NOT NULL,
  `latitude` decimal(10,8) DEFAULT NULL,
  `longitude` decimal(11,8) DEFAULT NULL,
  `GoodForDancing` tinyint(1) DEFAULT NULL,
  `BusinessParking_valet` tinyint(1) DEFAULT NULL,
  `Open24Hours` tinyint(1) DEFAULT NULL,
  `RestaurantsDelivery` tinyint(1) DEFAULT NULL,
  `Ambience_hipster` tinyint(1) DEFAULT NULL,
  `BYOBCorkage` tinyint(1) DEFAULT NULL,
  `GoodForMeal_lunch` tinyint(1) DEFAULT NULL,
  `RestaurantsAttire` tinyint(1) DEFAULT NULL,
  `RestaurantsTableService` tinyint(1) DEFAULT NULL,
  `BusinessParking` tinyint(1) DEFAULT NULL,
  `Ambience_romantic` tinyint(1) DEFAULT NULL,
  `AgesAllowed` tinyint(1) DEFAULT NULL,
  `HappyHour` tinyint(1) DEFAULT NULL,
  `RestaurantsReservations` tinyint(1) DEFAULT NULL,
  `BusinessParking_validated` tinyint(1) DEFAULT NULL,
  `DogsAllowed` tinyint(1) DEFAULT NULL,
  `Ambience_divey` tinyint(1) DEFAULT NULL,
  `BusinessAcceptsCreditCards` tinyint(1) DEFAULT NULL,
  `ByAppointmentOnly` tinyint(1) DEFAULT NULL,
  `Alcohol` tinyint(1) DEFAULT NULL,
  `Caters` tinyint(1) DEFAULT NULL,
  `NoiseLevel` tinyint(1) DEFAULT NULL,
  `GoodForKids` tinyint(1) DEFAULT NULL,
  `BusinessParking_street` tinyint(1) DEFAULT NULL,
  `HairSpecializesIn` tinyint(1) DEFAULT NULL,
  `RestaurantsPriceRange2` tinyint(1) DEFAULT NULL,
  `BusinessAcceptsBitcoin` tinyint(1) DEFAULT NULL,
  `DietaryRestrictions` tinyint(1) DEFAULT NULL,
  `GoodForMeal_latenight` tinyint(1) DEFAULT NULL,
  `RestaurantsCounterService` tinyint(1) DEFAULT NULL,
  `BestNights` tinyint(1) DEFAULT NULL,
  `BYOB` tinyint(1) DEFAULT NULL,
  `RestaurantsTakeOut` tinyint(1) DEFAULT NULL,
  `Ambience_upscale` tinyint(1) DEFAULT NULL,
  `GoodForMeal_breakfast` tinyint(1) DEFAULT NULL,
  `Ambience` tinyint(1) DEFAULT NULL,
  `OutdoorSeating` tinyint(1) DEFAULT NULL,
  `AcceptsInsurance` tinyint(1) DEFAULT NULL,
  `GoodForMeal_brunch` tinyint(1) DEFAULT NULL,
  `WheelchairAccessible` tinyint(1) DEFAULT NULL,
  `Music` tinyint(1) DEFAULT NULL,
  `Ambience_trendy` tinyint(1) DEFAULT NULL,
  `DriveThru` tinyint(1) DEFAULT NULL,
  `BikeParking` tinyint(1) DEFAULT NULL,
  `Ambience_touristy` tinyint(1) DEFAULT NULL,
  `GoodForMeal` tinyint(1) DEFAULT NULL,
  `BusinessParking_lot` tinyint(1) DEFAULT NULL,
  `CoatCheck` tinyint(1) DEFAULT NULL,
  `Corkage` tinyint(1) DEFAULT NULL,
  `HasTV` tinyint(1) DEFAULT NULL,
  `RestaurantsGoodForGroups` tinyint(1) DEFAULT NULL,
  `Ambience_classy` tinyint(1) DEFAULT NULL,
  `BusinessParking_garage` tinyint(1) DEFAULT NULL,
  `GoodForMeal_dinner` tinyint(1) DEFAULT NULL,
  `GoodForMeal_dessert` tinyint(1) DEFAULT NULL,
  `Ambience_intimate` tinyint(1) DEFAULT NULL,
  `WiFi` tinyint(1) DEFAULT NULL,
  `Ambience_casual` tinyint(1) DEFAULT NULL,
  `Smoking` tinyint(1) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `business_reviews` (
  `id_review` int(11) NOT NULL,
  `business_id` int(11) NOT NULL,
  `stars` float DEFAULT NULL,
  `review_date` date DEFAULT NULL,
  `text_review` text DEFAULT NULL,
  `positive_sentiment` tinyint(1) DEFAULT NULL,
  `neutral_sentiment` tinyint(1) DEFAULT NULL,
  `negative_sentiment` tinyint(1) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
--
-- Estructura de tabla para la tabla `counties`
--

CREATE TABLE `counties` (
  `id_county` int(11) NOT NULL,
  `name_county` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
--
-- Indices de la tabla `businesses`
--
ALTER TABLE `businesses`
  ADD PRIMARY KEY (`business_id`),
  ADD KEY `city_id` (`county_id`);

--
-- Indices de la tabla `business_reviews`
--
ALTER TABLE `business_reviews`
  ADD PRIMARY KEY (`id_review`),
  ADD KEY `business_reviews_ibfk_1` (`business_id`);

--
-- Indices de la tabla `counties`
--
ALTER TABLE `counties`
  ADD PRIMARY KEY (`id_county`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `businesses`
--
ALTER TABLE `businesses`
  MODIFY `business_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=473;

--
-- AUTO_INCREMENT de la tabla `business_reviews`
--
ALTER TABLE `business_reviews`
  MODIFY `id_review` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7808;

--
-- AUTO_INCREMENT de la tabla `counties`
--
ALTER TABLE `counties`
  MODIFY `id_county` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=197;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `businesses`
--
ALTER TABLE `businesses`
  ADD CONSTRAINT `businesses_ibfk_1` FOREIGN KEY (`county_id`) REFERENCES `counties` (`id_county`);

--
-- Filtros para la tabla `business_reviews`
--
ALTER TABLE `business_reviews`
  ADD CONSTRAINT `business_reviews_ibfk_1` FOREIGN KEY (`business_id`) REFERENCES `businesses` (`business_id`) ON DELETE NO ACTION ON UPDATE NO ACTION;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
