grape-tester
============
��� ������ ��� ������������ ������ �elliptics + cocaine + grape.

����� ����� ������
==================
���� ���� ������� ������ � ��������� ����� ��� ��� � elliptics'��. ������ ������������� � �������
apt ��������� ������ ������� �� ������� ������ � �� ���� � elliptics'��. ��� ������� ������ � ��� ���
������ ������� ���������. ����� ������ ��������� �� ����� ���������. �� ������ � ������ ���� ��
�������� � �������� � cocaine �������� ����������. ����� ������ ���������
������������ ������ ��������� ����������, ��������� ������ elliptics'� �� ����� � ��������� �
�������� ����������� ����� �� ���� ���.

�����
=====
* main_tester.py - ����� ������� ������. �� �������� �� ������� ������ � ��������� ���� ������ ���. ��������� main_tester.py --help ��� �������.
* node_tester.py - ������, ������� �������� �� �����. ������� ��� �� �����.

* main_config.py - ������ ��� ������� ������. ���������� ���� ���������� ������������������ � ����� ������� ��� ��������.
* node_config.py - ������ ��� ��� � elliptics'��.
��, ��� ������� - ��� ������ �� ������.

* common/ - ������ ��������� ������, ������� ���������� � main_tester.py, � node_tester.py.
* main_node/ - ������, ������� ���������� ������ main_tester.py.
* templates/ - ��� ����� ������� ������ ���������������� ������ ��� elliptics'� � cocaine'�.

������� ����� � ����� �������������, ���� ��� ����� �����-�� ������ ������������.
����� ���� <{VAR}> - ��� ����������, ������ ������� � �������� ������ ����� ���-�� ������������.
������ ������ ����� ���������� �� ����������, �.�. � �� �������� �� ���� ����������. �� �� ����� ���������� � ���� ������� main_tester.py.

�������������
=============
������ ��������� ��������� ������� �� �������� �� �����������������. ������� � ������������, ���
������� ������ �������� �� �����, ������ ���� ����� �� ������������� sudo ��� ������.

��� �� � ������� ������ ���� ������ �� ���� �� ssh ��� ������. ������� �� ����� ����� ���������
�������������� �� �����. ���� � ��������� ������ ����� ������� ������� ����� �������� -k, � �������
��� ������ ������ �� ������, ���� ssh ��� � ��� ������ (���� ��� ~/.ssh/id_rsa ��� �� �������� � ~/.ssh/config � �.�.).

������ ��� � ���������� ����� ������� � main_config.py.

������ ����� ��������� main_tester.py � ������������� grape.

