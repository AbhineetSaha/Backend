import java.util.*;
import java.util.concurrent.Semaphore;
public class Main {
    static Semaphore s = new Semaphore(1);
    static Semaphore f = new Semaphore(0);
    static Semaphore e = new Semaphore(5);

    public static void producer() {
        while(true) {
            try {
                e.acquire();
                s.acquire();
                System.out.println("produced");
            } catch (InterruptedException ex) {
                Thread.currentThread().interrupt();
                return;
            }
            s.release();
            f.release();
        }
    }

    public static void consumer() {
        while(true) {
            try {
                f.acquire();
                s.acquire();
                System.out.println("consumed");
            } catch (InterruptedException ex) {
                Thread.currentThread().interrupt();
                return;
            }
            s.release();
            e.release();
        }
    }

    public static void main(String[] args) {
        new Thread(() -> producer()).start();
        new Thread(() -> consumer()).start();
    }
}
