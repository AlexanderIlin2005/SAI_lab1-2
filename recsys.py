import subprocess
import re
import os
import signal
import sys


class SimplePrologExecutor:
    def __init__(self, prolog_file):
        self.prolog_file = os.path.abspath(prolog_file)
        self.process = None

    def execute_query(self, prolog_query):
        commands = [
            f'consult("{self.prolog_file}").',
            f'({prolog_query}), format("RESULT: "), writeq(X), format("~n"), fail.',
            'format("END").',
            'halt.'
        ]

        full_script = '\n'.join(commands)

        try:
            self.process = subprocess.Popen(
                ['swipl', '-q'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = self.process.communicate(input=full_script, timeout=10)
            return self._parse_output(stdout)

        except subprocess.TimeoutExpired:
            if self.process:
                self.process.terminate()
            return "Таймаут запроса"
        except Exception as e:
            if self.process:
                self.process.terminate()
            return f"Ошибка: {e}"
        finally:
            self.process = None

    def _parse_output(self, output):
        if not output:
            return "Нет результатов"

        lines = []
        for line in output.strip().split('\n'):
            if line.startswith('RESULT: '):
                result = line[8:].strip()
                if result and result != 'false':
                    formatted_result = self._format_result(result)
                    lines.append(f"  {formatted_result}")

        return '\n'.join(lines) if lines else "Нет результатов"

    def _format_result(self, result):
        if result.startswith('class_boss_weapon('):
            match = re.match(r'class_boss_weapon\(([^,]+),([^,]+),([^)]+)\)', result)
            if match:
                class_name, boss, weapon = match.groups()
                return f"Класс: {class_name}, Босс: {boss}, Оружие: {weapon}"

        elif result.startswith('info('):
            match = re.match(r'info\(([^,]+),([^,]+),([^)]+)\)', result)
            if match:
                item, prop1, prop2 = match.groups()
                return f"{item}: {prop1}, {prop2}"

        return result

    def cleanup(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None


class DialogueManager:
    def __init__(self, prolog_executor):
        self.prolog = prolog_executor
        self.user_profile = {}

    def start_dialogue(self):
        print("Добро пожаловать в систему рекомендаций Elden Ring!")
        print("Я помогу вам подобрать подходящий класс, оружие и боссов.")

        self._collect_user_preferences()
        self._provide_recommendations()

    def _collect_user_preferences(self):
        print("\nДавайте узнаем о ваших предпочтениях в игре!")

        # Стиль игры
        print("\n1. Какой стиль игры вам больше нравится?")
        print("   - ближний бой")
        print("   - магия")
        print("   - гибридный")
        print("   - стелс")
        print("   - дальний бой")
        print("   - призыв существ")

        while True:
            style = input("Ваш выбор: ").strip().lower()

            style_prolog = style.replace(' ', '_')
            prolog_query = f'стиль_игры({style_prolog})'
            result = self.prolog.execute_query(prolog_query)
            if "Нет результатов" not in result:
                self.user_profile['style'] = style_prolog
                break
            else:
                print("Такого стиля нет в игре. Попробуйте еще раз.")


        print("\n2. Какой у вас опыт в подобных играх?")
        print("   - новичок")
        print("   - опытный")

        while True:
            experience = input("Ваш уровень: ").strip().lower()
            if experience in ['новичок', 'опытный']:
                self.user_profile['experience'] = experience
                break
            else:
                print("Пожалуйста, выберите из предложенных вариантов.")


        print("\n3. Какие характеристики вам больше нравятся?")
        print("   - сила")
        print("   - ловкость")
        print("   - интеллект")
        print("   - вера")
        print("   - телосложение")
        print("   - выносливость")

        attributes = []
        print("Введите характеристики через запятую (например: сила, ловкость):")
        user_attrs = input("Ваш выбор: ").strip().lower()
        for attr in user_attrs.split(','):
            attr = attr.strip()
            prolog_query = f'атрибут({attr})'
            result = self.prolog.execute_query(prolog_query)
            if "Нет результатов" not in result:
                attributes.append(attr)

        self.user_profile['attributes'] = attributes

    def _provide_recommendations(self):
        print("\nНа основе ваших предпочтений, вот мои рекомендации:")


        self._recommend_classes()


        self._recommend_weapons()


        self._recommend_bosses()


        self._additional_recommendations()

    def _recommend_classes(self):
        print("\nПОДХОДЯЩИЕ КЛАССЫ:")


        style = self.user_profile['style']
        prolog_query = f'рекомендовать_класс({style}, X)'
        result_style = self.prolog.execute_query(prolog_query)


        result_attrs = "Нет результатов"
        classes_by_style = []
        classes_by_attrs = []

        if self.user_profile['attributes']:
            attrs = self.user_profile['attributes']
            conditions = ', '.join([f'имеет_атрибут(X, {attr})' for attr in attrs])
            prolog_query = f'класс(X), {conditions}'
            result_attrs = self.prolog.execute_query(prolog_query)


        if "Нет результатов" not in result_style:
            classes_by_style = [line.strip() for line in result_style.split('\n') if line.strip()]

        if "Нет результатов" not in result_attrs:
            classes_by_attrs = [line.strip() for line in result_attrs.split('\n') if line.strip()]


        intersection_classes = set(classes_by_style) & set(classes_by_attrs)


        if "Нет результатов" not in result_style:
            display_style = style.replace('_', ' ')
            print(f"По стилю '{display_style}':")
            print(result_style)

        if "Нет результатов" not in result_attrs:
            attrs = self.user_profile['attributes']
            print(f"По характеристикам {attrs}:")
            print(result_attrs)


        if intersection_classes:
            print("Наиболее подходящие классы (удовлетворяют обоим критериям):")
            for cls in intersection_classes:
                print(f"  {cls}")

    def _recommend_weapons(self):
        print("\nРЕКОМЕНДУЕМОЕ ОРУЖИЕ:")

        style = self.user_profile['style']
        prolog_query = f'рекомендовать_оружие_для_стиля({style}, X)'
        result = self.prolog.execute_query(prolog_query)
        if "Нет результатов" not in result:
            print(result)

    def _recommend_bosses(self):
        print("\nРЕКОМЕНДУЕМЫЕ БОССЫ:")

        experience = self.user_profile['experience']
        if experience == 'новичок':
            prolog_query = 'рекомендовать_стартового_босса(X)'
        else:
            prolog_query = 'рекомендовать_сложного_босса(X)'

        result = self.prolog.execute_query(prolog_query)
        if "Нет результатов" not in result:
            print(result)

    def _additional_recommendations(self):
        print("\nДОПОЛНИТЕЛЬНЫЕ РЕКОМЕНДАЦИИ:")


        style = self.user_profile['style']
        prolog_query = f'рекомендовать_заклинания_для_стиля({style}, X)'
        result = self.prolog.execute_query(prolog_query)
        if "Нет результатов" not in result:
            display_style = style.replace('_', ' ')
            print(f"Заклинания для стиля '{display_style}':")
            print(result)


        if self.user_profile['experience'] == 'новичок':
            prolog_query = 'рекомендовать_для_новичка(Class, Boss, Weapon), X=class_boss_weapon(Class,Boss,Weapon)'
            result = self.prolog.execute_query(prolog_query)
            if "Нет результатов" not in result:
                print("Полная сборка для начала игры:")
                print(result)


class QueryParser:
    TEMPLATES = [
        (r'классы для (.+)', 'рекомендовать_класс({}, X)'),
        (r'оружие для (.+)', 'рекомендовать_оружие_для_стиля({}, X)'),
        (r'заклинания для (.+)', 'рекомендовать_заклинания_для_стиля({}, X)'),
        (r'боссы для (новичок|начинающий)', 'рекомендовать_стартового_босса(X)'),
        (r'боссы для (опытный|эксперт)', 'рекомендовать_сложного_босса(X)'),
        (r'все классы', 'класс(X)'),
        (r'все боссы', 'босс(X)'),
        (r'все оружие', 'оружие(X)'),
        (r'все стили', 'стиль_игры(X)'),
        (r'все заклинания', 'заклинание(X)'),
    ]

    @classmethod
    def parse_to_prolog(cls, user_input):
        user_input_lower = user_input.lower().strip()

        if 'класс с' in user_input_lower:
            match = re.match(r'класс с (.+)', user_input_lower)
            if match:
                attrs = match.group(1).split(' и ')
                # Заменяем пробелы на подчеркивания в атрибутах
                processed_attrs = [attr.strip().replace(' ', '_') for attr in attrs]
                conditions = ', '.join([f'имеет_атрибут(X, {attr})' for attr in processed_attrs])
                return f'класс(X), {conditions}'

        if 'рекомендация для новичка' in user_input_lower:
            return 'рекомендовать_для_новичка(Class, Boss, Weapon), X=class_boss_weapon(Class,Boss,Weapon)'

        if 'инфо о классах' in user_input_lower or 'информация о классах' in user_input_lower:
            return 'класс(Class), предпочитает_стиль(Class, Style), имеет_атрибут(Class, Attr), X=info(Class,Style,Attr)'

        if 'инфо о боссах' in user_input_lower or 'информация о боссах' in user_input_lower:
            return 'босс(Boss), находится_в(Boss, Location), сложность(Boss, Difficulty), X=info(Boss,Location,Difficulty)'

        for pattern, prolog_template in cls.TEMPLATES:
            match = re.match(pattern, user_input_lower)
            if match:
                if '{}' in prolog_template:
                    # Заменяем пробелы на подчеркивания в группах
                    processed_groups = [group.replace(' ', '_') for group in match.groups()]
                    return prolog_template.format(*processed_groups)
                else:
                    return prolog_template

        keyword_queries = {
            'класс': 'класс(X)',
            'босс': 'босс(X)',
            'оружие': 'оружие(X)',
            'стиль': 'стиль_игры(X)',
            'заклинание': 'заклинание(X)'
        }

        for keyword, query in keyword_queries.items():
            if keyword in user_input_lower:
                return query

        return 'рекомендовать_для_новичка(Class, Boss, Weapon), X=class_boss_weapon(Class,Boss,Weapon)'


def signal_handler(sig, frame):
    print("\nЗавершение работы...")
    if 'prolog' in globals():
        prolog.cleanup()
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, signal_handler)

    prolog_file = "labprolog.pl"

    if not os.path.exists(prolog_file):
        print(f"Файл {prolog_file} не найден!")
        return

    global prolog
    prolog = SimplePrologExecutor(prolog_file)

    examples = [
        "классы для ближний бой",
        "оружие для магия",
        "боссы для новичок",
        "класс с сила и телосложение",
        "инфо о классах",
        "все классы",
        "рекомендация для новичка",
        "диалог",
        "выход"
    ]

    print("Система рекомендаций Elden Ring")
    print("Доступные команды:")
    print("  'старт' - начать интерактивный подбор")
    print("  'примеры' - показать примеры запросов")
    print("  'выход' - завершить работу")

    try:
        while True:
            user_input = input("\nВаш запрос: ").strip()

            if user_input.lower() in ['выход', 'exit', 'quit']:
                print("До свидания!")
                break

            if not user_input:
                continue

            if user_input.lower() == 'примеры':
                print("\nПримеры запросов:")
                for example in examples:
                    print(f"  {example}")
                continue

            if user_input.lower() == 'start':
                dialogue_manager = DialogueManager(prolog)
                dialogue_manager.start_dialogue()
                continue

            prolog_query = QueryParser.parse_to_prolog(user_input)
            print(f"Prolog запрос: {prolog_query}")

            result = prolog.execute_query(prolog_query)
            print(f"\nРезультат:\n{result}")

    except KeyboardInterrupt:
        print("\nЗавершение работы...")
    finally:
        prolog.cleanup()


if __name__ == "__main__":
    main()