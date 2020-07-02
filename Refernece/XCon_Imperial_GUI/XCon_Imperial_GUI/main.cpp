#include "xcon_imperial.h"
#include <QApplication>

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);
    XCon_Imperial w;
    w.show();

    return a.exec();
}
