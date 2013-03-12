grape-tester
============
Это скрипт для тестирования связки  elliptics + cocaine + grape.

Общая схема работы
==================
Есть одна главная машина и несколько машин для нод с elliptics'ом. Скрипт устанавливает с помощью
apt некоторый список пакетов на главную машину и на ноды с elliptics'ом. Для главной машины и для нод
списки пакетов отдельные. Затем скрипт запускает на нодах еллиптикс. На первой в списке ноде он
собирает и аплоадит в cocaine тестовое приложение. Далее скрипт тестирует
правильность работы тестового приложения, завершает демоны elliptics'а на нодах и загружает в
домашнюю дирректорию файлы со всех нод.

Файлы
=====
* main_tester.py - самый главный скрипт. Он работает на главной машине и запускать надо именно его. Выполните main_tester.py --help для справки.
* node_tester.py - скрипт, который работает на нодах. Трогать его не стоит.
* main_config.py - конфиг для главной машины. Назначение всех параметров прокомментированно в самом конфиге или очевидно.
* node_config.py - конфиг для нод с elliptics'ом.

Да, оба конфига - это модули на питоне.

* common/ - всякие служебные модули, которые используют и main_tester.py, и node_tester.py.
* main_node/ - модули, которые использует только main_tester.py.
* templates/ - тут лежат шаблоны всяких конфигурационных файлов для elliptics'а и cocaine'а.

Шаблоны можно и нужно редактировать, если вам нужна какая-то другая конфигурация.
Текст типа <{VAR}> - это переменная, вместо которой в реальный конфиг будет что-то подставленно.
Полный список таких переменных не фиксирован, т.к. я их добавлял по мере надобности. Но их можно посмотреть в коде скрипта main_tester.py.

Использование
=============
Скрипт выполняет некоторые команды на серверах от суперпользователя. Поэтому у пользователя, под
которым скрипт работает на нодах, должны быть права на использование sudo без пароля.

Так же у скрипта должен быть доступ на ноды по ssh без пароля. Поэтому на нодах нужно настроить
аутентификацию по ключу. Файл с приватным ключом можно указать скрипту через параметр -k, в конфиге
или просто ничего не делать, если ssh его и так найдет (если это ~/.ssh/id_rsa или он прописан в ~/.ssh/config и т.п.).

Адреса нод с элептиксом нужно вписать в main_config.py. Запускать main_tester.py можно от любого
пользователя, а пользователя на нодах нужно вписать в main_config.py.

Теперь можно запустить main_tester.py и потестировать grape.
