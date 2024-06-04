#!/bin/bash

echo Впиши токен telegram бота

read vartoken

echo $vartoken > tokens/telegram.txt

echo Токен записан

echo Впиши ID админа

read varadmin

echo $varadmin > tokens/admin.txt

echo ID админа записан

echo Установка зависимостей

poetry update

echo Зависимости установлены

echo Формирование базы

echo К запуску готов