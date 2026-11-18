import java.io.File;
import com.cburch.logisim.circuit.Circuit;
import com.cburch.logisim.comp.Component;
import com.cburch.logisim.comp.EndData;
import com.cburch.logisim.data.Location;
import com.cburch.logisim.file.Loader;
import com.cburch.logisim.file.LogisimFile;

/** Prints every component's port locations, and flags ports that touch nothing. */
public class PortDump {
    public static void main(String[] args) throws Exception {
        LogisimFile file = new Loader(null).openLogisimFile(new File(args[0]));
        boolean dangling = args.length > 1 && args[1].equals("dangling");
        int problems = 0;
        for (Circuit c : file.getCircuits()) {
            for (Component comp : c.getNonWires()) {
                StringBuilder sb = new StringBuilder();
                for (EndData e : comp.getEnds()) {
                    Location l = e.getLocation();
                    int n = c.getComponents(l).size();
                    if (n < 2 && e.isInput()) { problems++; if (dangling) System.out.println("DANGLING " + c.getName() + " :: "
                            + comp.getFactory().getName() + " port at " + l); }
                    sb.append(" ").append(l.getX() - comp.getLocation().getX()).append(",")
                      .append(l.getY() - comp.getLocation().getY());
                }
                if (!dangling) System.out.println(c.getName() + " | " + comp.getFactory().getName() + " @"
                        + comp.getLocation() + " |" + sb);
            }
        }
        if (dangling) System.out.println("DANGLING_TOTAL " + problems);
        System.exit(0);
    }
}
