import unittest

from mod.reports.report_menu_catalog import DropdownMenuManager


class DropdownMenuManagerTests(unittest.TestCase):
    def setUp(self):
        self.manager = DropdownMenuManager()

    def test_mode_menu_contains_requested_items(self):
        self.assertEqual(self.manager.get_mode_menu_name(), "Режимы")
        self.assertEqual(
            self.manager.get_mode_menu_items(),
            [
                "Книга записи на прием",
                "Пациенты",
                "Практика",
                "Маркетинг",
                "Страхование",
                "Настройка",
                "Лаборатории",
                "Стационар",
                "Аналитика",
                "Главное меню",
                "Настройка принтера...",
                "Настройка принтеров для печати документов...",
                "Время работы - ВКЛЮЧИТЬ ЧАСЫ",
                "Время работы - ОСТАНОВИТЬ ЧАСЫ",
                "Выход из Dental 4 Windows SQL",
            ],
        )

    def test_mode_shortcuts_format_requested_paths(self):
        self.assertEqual(
            self.manager.format_mode_entry(0),
            "'режим' - tabmenu 'Режимы' - 'Книга записи на прием'",
        )
        self.assertEqual(
            self.manager.format_mode_entry(5),
            "'режим' - tabmenu 'Режимы' - 'Настройка'",
        )
        self.assertEqual(
            self.manager.format_mode_menu_entry("Лаборатории"),
            "'режим' - tabmenu 'Режимы' - 'Лаборатории'",
        )
        self.assertIn("Лаборатории", self.manager.get_mode_names())
        self.assertEqual(
            self.manager.format_mode_entry(6),
            "'режим' - tabmenu 'Режимы' - 'Лаборатории'",
        )
        self.assertEqual(
            self.manager.format_mode_button_entry(0),
            "'режим' - 'книга записи на прием'",
        )
        self.assertEqual(
            self.manager.format_mode_button_entry(5),
            "'режим' - 'Настройки'",
        )

    def test_appointment_menu_matches_requested_structure(self):
        self.assertEqual(
            self.manager.get_appointment_menu_names(),
            ["Режимы", "Вид", "Книги", "Опции", "Отчеты", "Помощь"],
        )
        self.assertEqual(
            self.manager.get_appointment_items("Режимы"),
            [
                "Аналитика",
                "Главное меню",
                "Настройка принтера...",
                "Настройка принтеров для печати документов...",
                "Время работы - ВКЛЮЧИТЬ ЧАСЫ",
                "Время работы - ОСТАНОВИТЬ ЧАСЫ",
                "Выход из Dental 4 Windows SQL",
            ],
        )
        self.assertEqual(
            self.manager.get_appointment_items("Вид"),
            [
                "Одна книга",
                "Горизонтальный",
                "Бригада",
                "Показать коды врачей",
                "Отображать книги записи в вых. дни",
            ],
        )
        self.assertEqual(self.manager.get_appointment_items("Книги"), ["Список..."])
        self.assertEqual(
            self.manager.get_appointment_items("Опции"),
            [
                "Обновить экран",
                "Поиск визитов пациента...",
                "Поиск свободного времени...",
                "Новое окно",
                "Карта занятости...",
                "Список ожидания...",
                "Список отменённых визитов",
                "Данные о времени визита...",
                "Настройка всех книг",
                "Расписание врачей",
                "Статусы...",
                "Функции статусов...",
                "Резервирования...",
                "Настройка классов...",
                "Онлайн запись",
                "Просмотр онлайн записей",
                "Отправить напоминания...",
            ],
        )
        self.assertEqual(
            self.manager.get_appointment_items("Отчеты"),
            [
                "Статус - отчет...",
                "Статус - отчет (нефинансовый)...",
                "Класс - отчет...",
                "Класс - отчет (нефинансовый)...",
                "Анализ рабочего времени",
                "Расписание на день (все книги)",
                "Записи на прием – кто записал",
                "Планируемый доход",
                "Учет времени посещений",
                "Пациенты без записей о лечении",
            ],
        )
        self.assertEqual(
            self.manager.get_appointment_items("Помощь"),
            [
                "Разделы помощи",
                "О программе",
                "Системная информация",
                "Регистрация",
            ],
        )

    def test_appointment_entries_use_exact_requested_format(self):
        self.assertEqual(
            self.manager.format_appointment_tab_entry("Режимы"),
            "'режим' - 'книга записи на прием' - tabmenu 'Режимы'",
        )
        self.assertEqual(
            self.manager.format_appointment_entry("Режимы", "Аналитика"),
            "'режим' - 'книга записи на прием' - tabmenu 'Режимы' - 'Аналитика'",
        )
        self.assertEqual(
            self.manager.format_appointment_entry("Вид", "Одна книга"),
            "'режим' - 'книга записи на прием' - tabmenu 'Вид' - 'Одна книга'",
        )
        self.assertEqual(
            self.manager.format_appointment_entry("Книги", "Список..."),
            "'режим' - 'книга записи на прием' - tabmenu 'Книги' - 'Список...'",
        )
        self.assertEqual(
            self.manager.format_appointment_entry("Помощь", "Регистрация"),
            "'режим' - 'книга записи на прием' - tabmenu 'Помощь' - 'Регистрация'",
        )

    def test_patient_common_info_matches_requested_tabs_and_items(self):
        self.assertEqual(
            self.manager.get_patient_tabs("Общ.сведения"),
            ["Режимы", "Поиск/Просмотр", "Пациенты"],
        )
        self.assertEqual(
            self.manager.get_patient_tab_items("Общ.сведения", "Режимы"),
            [
                "Книга записи на прием",
                "Пациенты",
                "Практика",
                "Маркетинг",
                "Страхование",
                "Настройка",
                "Лаборатории",
                "Стационар",
                "Аналитика",
                "Главное меню",
                "Настройка принтера...",
                "Настройка принтеров для печати документов...",
                "Время работы - ВКЛЮЧИТЬ ЧАСЫ",
                "Время работы - ОСТАНОВИТЬ ЧАСЫ",
                "Выход из Dental 4 Windows SQL",
            ],
        )
        self.assertEqual(
            self.manager.get_patient_tab_items("Общ.сведения", "Поиск/Просмотр"),
            [
                "Найти пациента...",
                "Выбрать поля результатов поиска пациента",
                "Просмотр пациента",
                "Просмотр семьи",
                "Список попечителей...",
                "История вызовов...",
                "В начало",
                "Предыдущ.",
                "Следующ.",
                "В конец",
                "Журнал связи",
                "Визиты пациента",
            ],
        )
        self.assertEqual(
            self.manager.get_patient_tab_items("Общ.сведения", "Пациенты"),
            [
                "Новый глава семьи",
                "Новый член семьи",
                "Импорт пациентов",
                "Обновить",
                "Отчет о данных пациента",
                "Отключить заглавные буквы",
                "Отключить список",
                "Фотография",
                "Удалить фотографию",
                "Объединить с другим пациентом...",
                "Удалить пациента",
                "Отправить SMS",
            ],
        )

    def test_patient_common_info_entries_use_requested_format(self):
        self.assertEqual(
            self.manager.format_patient_tab_item_entry("Общ.сведения", "Режимы", "Книга записи на прием"),
            "'режим' - 'Пациенты' - 'Общ.сведения' - tabmenu 'Режимы' - 'Книга записи на прием'",
        )
        self.assertEqual(
            self.manager.format_patient_tab_item_entry("Общ.сведения", "Поиск/Просмотр", "Выбрать поля результатов поиска пациента"),
            "'режим' - 'Пациенты' - 'Общ.сведения' - tabmenu 'Поиск/Просмотр' - 'Выбрать поля результатов поиска пациента'",
        )
        self.assertEqual(
            self.manager.format_patient_tab_item_entry("Общ.сведения", "Пациенты", "Отправить SMS"),
            "'режим' - 'Пациенты' - 'Общ.сведения' - tabmenu 'Пациенты' - 'Отправить SMS'",
        )

    def test_karta_zubov_matches_requested_update(self):
        self.assertIn("Карта", self.manager.get_patient_tabs("Карта зубов"))
        self.assertIn("Состояния", self.manager.get_patient_tabs("Карта зубов"))
        self.assertEqual(
            self.manager.get_patient_tab_items("Карта зубов", "Карта"),
            [
                "Новая карта",
                "Новая карта (настраиваемая)",
                "Изменить дату/время/автора",
                "Обновить",
                "Копировать из других карт",
                "Создать альтернативную карту",
                "Запустить Digora",
                "Просмотр и печать экрана",
                "Просмотр примечаний к карте зубов",
                "Показывать детские карты",
                "Показывать подростковые карты",
                "Удалить процедуру",
                "Удалить карту целиком...",
                "Установить текущего врача как врача карты",
                "Показывать активную Карту по умолчанию",
                "Без планирования",
                "Показывать величины CPITN",
                "Просмотр истории примечаний",
            ],
        )
        self.assertEqual(
            self.manager.get_patient_tab_items("Карта зубов", "Состояния"),
            [
                "Примечание к выбранному зубу...",
                "Выпавший зуб",
                "Восстановить выпавший зуб",
                "Все выпавшие зубы",
                "Все выпавшие верхние зубы",
                "Все выпавшие нижние зубы",
                "Все выпавшие зубы мудрости",
                "Восстановить все выпавшие зубы",
                "Восстановите все верхние выпавшие зубы",
                "Восстановите все нижние выпавшие зубы",
                "Восстановите все выпавшие зубы мудрости",
                "Состояние",
                "Движение",
            ],
        )

    def test_parodont_matches_requested_update(self):
        self.assertEqual(
            self.manager.get_patient_tab_items("Пародонт", "Карта"),
            [
                "Новая карта пародонта",
                "Новая карта пародонта (настраиваемая)",
                "Изменить дату/время/автора",
                "Обновить",
                "Копировать из других карт пародонта",
                "Запустить Digora",
                "Просмотр и печать экрана",
                "Удалить зуб",
                "Восстановить удаленный зуб",
                "Удалить эту карту пародонта",
                "Установить текущего врача как врача карты пародонта",
                "Порядок обхода карты пародонта",
            ],
        )

    def test_plan_lechenia_matches_requested_update(self):
        plan_tabs = self.manager.get_patient_tabs("План лечения")
        self.assertIn("План лечения", plan_tabs)
        self.assertIn("Счета", plan_tabs)
        self.assertIn("Тех. работы", plan_tabs)
        self.assertEqual(
            self.manager.get_patient_tab_items("План лечения", "План лечения"),
            [
                "Новый план лечения",
                "Новый план лечения (настраиваемый)",
                "Изменить дату/время/автора",
                "Создать альтернативный план лечения",
                "Обновить",
                "Просмотр примечаний к плану",
                "Просмотр истории примечаний",
                "Печать плана",
                "Просмотр плана...",
                "Печать плана (только невыполненные процедуры)...",
                "Просмотр плана (только невыполненные процедуры)...",
                "Требование к страх.компании (стом.)",
                "Требование к страх.компании (мед.)",
                "Запустить Digora",
                'Удалить информацию о визитах пациента (колонка "Виз")',
                "Показывать активный План лечения по умолчанию",
                "Пересчитать компенсацию по страховке",
                "Пересчитать тариф для выбранной записи согласно текущему уровню расценок",
                "Пересчитать тариф для всех записей согласно текущему уровню расценок",
                "Копировать-вставить запись",
                "Удалить выделенную запись",
                "Удалить план",
                "Редактировать диагнозы...",
            ],
        )
        self.assertEqual(
            self.manager.get_patient_tab_items("План лечения", "Счета"),
            [
                "Создание счета...",
                "Создание счета с оплатой...",
            ],
        )
        self.assertEqual(
            self.manager.get_patient_tab_items("План лечения", "Тех. работы"),
            [
                "Новый заказ наряд...",
                "Заказ-наряды...",
            ],
        )

    def test_patient_updated_entries_use_requested_format(self):
        self.assertEqual(
            self.manager.format_patient_tab_item_entry("Карта зубов", "Карта", "Показывать величины CPITN"),
            "'режим' - 'Пациенты' - 'Карта зубов' - tabmenu 'Карта' - 'Показывать величины CPITN'",
        )
        self.assertEqual(
            self.manager.format_patient_tab_item_entry("Карта зубов", "Состояния", "Движение"),
            "'режим' - 'Пациенты' - 'Карта зубов' - tabmenu 'Состояния' - 'Движение'",
        )
        self.assertEqual(
            self.manager.format_patient_tab_item_entry("План лечения", "Счета", "Создание счета с оплатой..."),
            "'режим' - 'Пациенты' - 'План лечения' - tabmenu 'Счета' - 'Создание счета с оплатой...'",
        )

    def test_practice_menu_matches_requested_update(self):
        self.assertEqual(
            self.manager.get_practice_menu_names(),
            [
                "Врачи",
                "Персонал",
                "Банк.счета",
                "Выручка",
                "Отчеты",
                "Расценки",
                "Накладные",
                "Тарифы сотрудников",
                "Касса",
                "Управление SMS",
                "Автоматизация",
                "Бонусная система",
            ],
        )
        self.assertEqual(
            self.manager.get_practice_tab_items("Врачи", "Функции"),
            [
                "Новая запись",
                "Удалить",
                "Обновить",
                "Отключить заглавные буквы",
                "Табель учёта...",
                "Нормативы выработки...",
                "Перечень должностей...",
                "Настройка типов расценок",
                "Показывать неработающих специалистов",
            ],
        )
        self.assertEqual(
            self.manager.get_practice_tab_items("Персонал", "Функции"),
            [
                "Новая запись",
                "Удалить",
                "Обновить",
                "Отключить заглавные буквы",
                "Перечень должностей...",
                "Показывать неработающих сотрудников",
            ],
        )
        self.assertEqual(
            self.manager.get_practice_tab_items("Банк.счета", "Функции"),
            [
                "Обновить",
                "Показывать скрытые банковские счета",
                "Показывать неработающих специалистов",
            ],
        )
        self.assertEqual(
            self.manager.get_practice_tab_items("Выручка", "Выручка"),
            [
                "Новый документ...",
                "Новая EFT POS...",
                "Новая American Express...",
                "Новая Diners Club...",
                "Печать документа...",
                "Просмотр документа...",
                "Удаление документа",
                "Обновить",
                "Показывать скрытые банковские счета",
            ],
        )
        self.assertEqual(
            self.manager.get_practice_tab_items("Выручка", "Отчеты"),
            [
                "Печать данных о переводе",
                "Просмотр данных о переводе",
                "Отчет с данными о специалисте...",
                "Отчет с данными о специалисте и процентах...",
                "Все переводы за период",
                "Все платежи за период",
                "Все платежи за период по специалистам",
            ],
        )
        self.assertEqual(
            self.manager.get_practice_tab_items("Отчеты", "Функции"),
            [
                "Новый отчет",
                "Удалить отчет",
                "Редактировать отчет",
                "Обновить",
                "Настройка групп отчетов...",
                "Сводный отчет по КПЭ - Список ключевых процедур",
                'Настройка правил для "Лечения без плана" для КПЭ-01',
            ],
        )
        self.assertEqual(
            self.manager.get_practice_items("Автоматизация"),
            [
                "Выборки",
                "Запись на прием",
                "Вызовы",
                "Запросы",
            ],
        )
        self.assertEqual(
            self.manager.get_practice_items("Бонусная система"),
            [
                "Уровни",
                "Процедуры",
                "События",
            ],
        )
        self.assertEqual(
            self.manager.get_practice_tab_items("Бонусная система", "Функции"),
            [
                "Обновить",
                "Новая программа",
                "Показывать устаревшие программы",
                "Перемещение пациентов",
                "Отчет по начислениям бонусных баллов",
            ],
        )

    def test_practice_entries_use_requested_format(self):
        self.assertEqual(
            self.manager.format_practice_tab_item_entry("Врачи", "Функции", "Новая запись"),
            "'режим' - 'Практика' - 'Врачи' - tabmenu 'Функции' - 'Новая запись'",
        )
        self.assertEqual(
            self.manager.format_practice_tab_item_entry("Выручка", "Отчеты", "Все платежи за период"),
            "'режим' - 'Практика' - 'Выручка' - tabmenu 'Отчеты' - 'Все платежи за период'",
        )
        self.assertEqual(
            self.manager.format_practice_section_entry("Расценки"),
            "'режим' - 'Практика' - 'Расценки'",
        )
        self.assertEqual(
            self.manager.format_practice_item_entry("Автоматизация", "Выборки"),
            "'режим' - 'Практика' - 'Автоматизация' - 'Выборки'",
        )
        self.assertEqual(
            self.manager.format_practice_item_entry("Бонусная система", "События"),
            "'режим' - 'Практика' - 'Бонусная система' - 'События'",
        )

    def test_marketing_menu_matches_requested_update(self):
        self.assertEqual(
            self.manager.get_marketing_menu_names(),
            [
                "Вызовы",
                "Запросы",
                "Должники",
                "Коммуникации",
                "Потенциальные пациенты",
                "Сделки",
                "Настройки",
            ],
        )
        self.assertEqual(
            self.manager.get_marketing_tab_items("Запросы", "Запросы"),
            [
                "Создать запрос, определённый пользователем",
                "Редактировать запрос, определённый пользователем",
                "Удалить запрос, определённый пользователем",
                "Показывать неработающих специалистов",
            ],
        )
        self.assertEqual(
            self.manager.get_marketing_tab_items("Должники", "Должники"),
            [
                "Задержка напоминания 1",
                "Задержка напоминания 2",
                "Задержка напоминания 3",
                "Задержка напоминания 4",
                "Отмена задержки 1",
                "Отмена задержки 2",
                "Отмена задержки 3",
                "Отмена задержки 4",
                "Обновить",
                "Просмотр истории примечаний",
            ],
        )
        self.assertEqual(
            self.manager.get_marketing_tab_items("Должники", "Опции"),
            [
                "Печать счета...",
                "Просмотр счета...",
                "Установить/снять статус безнадежного счета",
                "Показывать неработающих специалистов",
            ],
        )
        self.assertEqual(
            self.manager.get_marketing_tab_items("Коммуникации", "Поиск/Просмотр"),
            [
                "Найти персону",
                "Сведения о персоне",
                "Коммуникации с персоной",
                "Запись на прием",
                "По контактным данным",
                "Коммуникации сотрудника",
                "Коммуникации врача",
            ],
        )
        self.assertEqual(
            self.manager.get_marketing_tab_items("Коммуникации", "Коммуникации"),
            [
                "Обновить",
                "Добавить запись",
                "Редактировать запись",
                "Удалить запись",
                "Новый потенциальный пациент",
                "Настройка внешних данных по коммуникациям",
                "Настройка обработки внешних данных",
                "Настройки вида",
            ],
        )
        self.assertEqual(
            self.manager.get_marketing_tab_items("Коммуникации", "Отчеты"),
            [
                "Экспорт в Excel",
                "Конверсия администраторов",
            ],
        )
        self.assertEqual(
            self.manager.get_marketing_tab_items("Потенциальные пациенты", "Потенциальные пациенты"),
            [
                "Найти потенциального пациента",
                "Добавить потенциального пациента",
                "Редактировать запись",
                "Удалить запись",
                "Запись на приём",
                "Новый глава семьи",
                "Новый член семьи",
                "Показать неактивных",
            ],
        )
        self.assertEqual(
            self.manager.get_marketing_tab_items("Сделки", "Поиск/Просмотр"),
            [
                "Найти контрагента",
                "Сведения внесенные на этапе",
                "Сведения о контрагенте",
                "Сделки с контрагентом",
                "Сделки сотрудника",
            ],
        )
        self.assertEqual(
            self.manager.get_marketing_tab_items("Сделки", "Сделки"),
            [
                "Обновить",
                "Показать / редактировать запись",
                "Удалить запись",
                "Настройка дополнительных полей сделки",
                "Настройки вида",
            ],
        )

    def test_marketing_entries_use_requested_format(self):
        self.assertEqual(
            self.manager.format_marketing_section_entry("Вызовы"),
            "'режим' - 'Маркетинг' - 'Вызовы'",
        )
        self.assertEqual(
            self.manager.format_marketing_tab_item_entry("Запросы", "Запросы", "Создать запрос, определённый пользователем"),
            "'режим' - 'Маркетинг' - 'Запросы' - tabmenu 'Запросы' - 'Создать запрос, определённый пользователем'",
        )
        self.assertEqual(
            self.manager.format_marketing_tab_item_entry("Коммуникации", "Отчеты", "Конверсия администраторов"),
            "'режим' - 'Маркетинг' - 'Коммуникации' - tabmenu 'Отчеты' - 'Конверсия администраторов'",
        )
        self.assertEqual(
            self.manager.format_marketing_tab_item_entry("Сделки", "Сделки", "Настройки вида"),
            "'режим' - 'Маркетинг' - 'Сделки' - tabmenu 'Сделки' - 'Настройки вида'",
        )

    def test_insurance_menu_matches_requested_update(self):
        self.assertEqual(
            self.manager.get_insurance_menu_names(),
            [
                "Сводные счета",
                "Платежи",
                "Сторонние организации",
            ],
        )
        self.assertEqual(
            self.manager.get_insurance_tab_items("Сводные счета", "Счета"),
            [
                "Создать сводный счёт",
                "Просмотр состава счёта",
                "Обновить",
            ],
        )
        self.assertEqual(
            self.manager.get_insurance_tab_items("Платежи", "Счета"),
            [
                "Просмотр состава счёта",
                "Регистрация оплаты счет",
                "Просмотр платежей",
                "Скидки",
                "Поместить счёт в архив",
                "Удаление счёта",
                "Печать счета",
                "Печать справки к счёту",
                "Печать счета фактуры",
                "Печать приложения к счёту",
                "Обновить",
            ],
        )
        self.assertEqual(
            self.manager.get_insurance_tab_items("Сторонние организации", "Функции"),
            [
                "Новая запись",
                "Удалить",
                "Обновить",
                "Отключить заглавные буквы",
            ],
        )

    def test_insurance_entries_use_requested_format(self):
        self.assertEqual(
            self.manager.format_insurance_tab_item_entry("Сводные счета", "Счета", "Создать сводный счёт"),
            "'режим' - 'Страхование' - 'Сводные счета' - tabmenu 'Счета' - 'Создать сводный счёт'",
        )
        self.assertEqual(
            self.manager.format_insurance_tab_item_entry("Платежи", "Счета", "Печать приложения к счёту"),
            "'режим' - 'Страхование' - 'Платежи' - tabmenu 'Счета' - 'Печать приложения к счёту'",
        )
        self.assertEqual(
            self.manager.format_insurance_tab_item_entry("Сторонние организации", "Функции", "Отключить заглавные буквы"),
            "'режим' - 'Страхование' - 'Сторонние организации' - tabmenu 'Функции' - 'Отключить заглавные буквы'",
        )

    def test_settings_menu_matches_requested_update(self):
        self.assertEqual(
            self.manager.get_settings_menu_names(),
            [
                "Практика",
                "Параметры",
                "Доступ",
                "Заболевания",
                "Заметки",
                "Материалы",
                "Процедуры",
                "Операции",
                "Справочники",
            ],
        )
        self.assertEqual(
            self.manager.get_settings_tab_items("Практика", "Функции"),
            [
                "Новая запись",
                "Отключить заглавные буквы",
                "Удалить запись",
                "Обновить",
                "Специализации...",
            ],
        )
        self.assertEqual(
            self.manager.get_settings_tab_items("Параметры", "Функции"),
            [
                "Обновить",
                "Поиск параметров ...",
            ],
        )
        self.assertEqual(
            self.manager.get_settings_tab_items("Доступ", "Функции"),
            [
                "Новая запись",
                "Изменить",
                "Удалить запись",
                "Обновить",
                "Снять все блокировки данных",
                "Очистить Список последних пациентов",
                "Печать списка прав доступа...",
                "Установка ограничений для паролей",
                "Настройка статусов режимов/функций...",
                "Аудит удаления записей...",
                'Показать "мертвые души"...',
                "Показать пользователей, которым закрыт доступ",
            ],
        )
        self.assertEqual(
            self.manager.get_settings_tab_items("Заболевания", "Функции"),
            [
                "Новая запись",
                "Отключить заглавные буквы",
                "Удалить запись",
                "Обновить",
                "Печать настроек...",
                "Показывать неактивные записи",
            ],
        )
        self.assertEqual(
            self.manager.get_settings_tab_items("Заметки", "Функции"),
            [
                "Новая запись",
                "Удалить запись",
                "Обновить",
                "Настройка категорий заметок",
                "Печать справочника...",
                "Показывать неработающих специалистов",
                "Копировать заметки от ...",
            ],
        )
        self.assertEqual(
            self.manager.get_settings_tab_items("Материалы", "Функции"),
            [
                "Отключить заглавные буквы",
                "Обновить",
                "Список поставщиков...",
                "Список материалов...",
                "Поиск материалов",
            ],
        )
        self.assertEqual(
            self.manager.get_settings_tab_items("Процедуры", "Функции"),
            [
                "Отключить заглавные буквы",
                "Обновить",
                "Настройка классификаторов процедур...",
                "Список процедур...",
                "Процедуры для Практик...",
                "Отчет : Расход материалов на процедуры",
                "Поиск процедуры",
            ],
        )

    def test_settings_entries_use_requested_format(self):
        self.assertEqual(
            self.manager.format_settings_tab_item_entry("Практика", "Функции", "Новая запись"),
            "'режим' - 'Настройки' - 'Практика' - tabmenu 'Функции' - 'Новая запись'",
        )
        self.assertEqual(
            self.manager.format_settings_tab_item_entry("Доступ", "Функции", "Снять все блокировки данных"),
            "'режим' - 'Настройки' - 'Доступ' - tabmenu 'Функции' - 'Снять все блокировки данных'",
        )
        self.assertEqual(
            self.manager.format_settings_tab_item_entry("Процедуры", "Функции", "Поиск процедуры"),
            "'режим' - 'Настройки' - 'Процедуры' - tabmenu 'Функции' - 'Поиск процедуры'",
        )
        self.assertEqual(
            self.manager.format_settings_section_entry("Операции"),
            "'режим' - 'Настройки' - 'Операции'",
        )
        self.assertEqual(
            self.manager.format_settings_section_entry("Справочники"),
            "'режим' - 'Настройки' - 'Справочники'",
        )

    def test_laboratories_menu_matches_requested_update(self):
        self.assertEqual(
            self.manager.get_laboratories_menu_names(),
            [
                "Лаборатории",
                "Персонал",
                "Расценки",
                "Заказы",
            ],
        )
        self.assertEqual(
            self.manager.get_laboratories_tab_items("Лаборатории", "Функции"),
            [
                "Новая запись",
                "Отключить заглавные буквы",
                "Удалить запись",
                "Обновить",
                "Показывать устаревшие лаборатории",
            ],
        )
        self.assertEqual(
            self.manager.get_laboratories_tab_items("Персонал", "Функции"),
            [
                "Новая запись",
                "Удалить",
                "Обновить",
                "Отключить заглавные буквы",
                "Перечень должностей...",
                "Показывать неработающих специалистов",
                "Показывать устаревшие лаборатории",
            ],
        )

    def test_laboratories_entries_use_requested_format(self):
        self.assertEqual(
            self.manager.format_laboratories_tab_item_entry("Лаборатории", "Функции", "Новая запись"),
            "'режим' - 'Лаборатории' - 'Лаборатории' - tabmenu 'Функции' - 'Новая запись'",
        )
        self.assertEqual(
            self.manager.format_laboratories_tab_item_entry("Персонал", "Функции", "Перечень должностей..."),
            "'режим' - 'Лаборатории' - 'Персонал' - tabmenu 'Функции' - 'Перечень должностей...'",
        )
        self.assertEqual(
            self.manager.format_laboratories_section_entry("Расценки"),
            "'режим' - 'Лаборатории' - 'Расценки'",
        )
        self.assertEqual(
            self.manager.format_laboratories_section_entry("Заказы"),
            "'режим' - 'Лаборатории' - 'Заказы'",
        )


if __name__ == "__main__":
    unittest.main()
