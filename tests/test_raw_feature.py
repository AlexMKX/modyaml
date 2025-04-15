#!/usr/bin/env python
"""
E2E тесты для проверки функциональности !raw и {% raw %} {% endraw %} в modyaml.
"""

import os
import sys
import unittest
import logging

# Добавляем родительскую директорию в sys.path для импорта локального модуля
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import modyaml


class TestRawFeatures(unittest.TestCase):
    """Тесты для проверки функций отключения интерполяции в modyaml."""

    @classmethod
    def setUpClass(cls):
        """Настройка окружения для всех тестов."""
        # Настраиваем логгирование
        logging.basicConfig(level=logging.DEBUG)
        os.environ['MODYAML_LOG_LEVEL'] = 'DEBUG'
        # Устанавливаем тестовую переменную окружения
        os.environ['TEST_VAR'] = 'test_value'
        # Путь к тестовому файлу
        cls.test_file = os.path.join(os.path.dirname(__file__), 'test_raw.yaml')

    def test_regular_interpolation(self):
        """Тест обычной интерполяции переменных окружения."""
        config = modyaml.load(self.test_file)
        self.assertEqual(config['regular_interpolation'], 'test_value')

    def test_raw_tag(self):
        """Тест тега !raw для отключения интерполяции."""
        config = modyaml.load(self.test_file)
        # Значение должно остаться необработанным шаблоном
        self.assertEqual(config['raw_content'], '{{ TEST_VAR }}')

    def test_raw_block(self):
        """Тест блоков {% raw %} {% endraw %} для отключения интерполяции."""
        config = modyaml.load(self.test_file)
        # Проверяем, что шаблоны внутри блока raw не были обработаны
        self.assertIn('{{ TEST_VAR }}', config['raw_block'])
        self.assertIn('{{ PATH }}', config['raw_block'])

    def test_mixed_content(self):
        """Тест совместного использования интерполяции и raw блоков."""
        config = modyaml.load(self.test_file)
        # Значение TEST_VAR должно быть заменено, а {{ необработанными }} должно остаться как есть
        self.assertIn('test_value', config['mixed_content'])
        self.assertIn('{{ необработанными }}', config['mixed_content'])

    def test_nested_values(self):
        """Тест вложенных значений с интерполяцией и !raw."""
        config = modyaml.load(self.test_file)
        # Проверяем, что вложенные значения обрабатываются правильно
        self.assertEqual(config['nested']['interpolated'], 'test_value')
        self.assertEqual(config['nested']['raw_value'], '{{ TEST_VAR }}')
        
    def test_include_with_raw(self):
        """Тест совместного использования !include и !raw."""
        config = modyaml.load(self.test_file)
        
        # Проверяем, что файл был включен
        self.assertIn('included', config)
        included = config['included']
        
        # Проверяем обычное значение с интерполяцией
        self.assertIn('test_value', included['value1'])
        
        # Проверяем значение с !raw без интерполяции
        self.assertEqual(included['raw_value'], 'Значение с необработанным {{ TEST_VAR }}')
        
        # Проверяем вложенное значение с интерполяцией
        self.assertIn('test_value', included['nested']['sub_value'])
        
    def test_nested_include(self):
        """Тест вложенных !include с !raw."""
        config = modyaml.load(self.test_file)
        
        # Получаем вложенный включенный файл
        nested_include = config['included']['nested_include']
        
        # Проверяем простое значение с интерполяцией
        self.assertIn('test_value', nested_include['simple_value'])
        
        # Проверяем !raw значение без интерполяции
        self.assertEqual(nested_include['nested_raw'], 'Необработанное вложенное {{ TEST_VAR }}')
        
        # Проверяем многоуровневое вложение
        level2 = nested_include['level1']['level2']
        self.assertIn('test_value', level2['interpolated'])
        self.assertEqual(level2['raw'], 'Двойное вложение без интерполяции {{ TEST_VAR }}')


if __name__ == '__main__':
    unittest.main() 