import java.io.*;
import java.util.*;

import com.cburch.logisim.circuit.Analyze;
import com.cburch.logisim.circuit.Circuit;
import com.cburch.logisim.circuit.CircuitState;
import com.cburch.logisim.circuit.Propagator;
import com.cburch.logisim.data.Value;
import com.cburch.logisim.file.Loader;
import com.cburch.logisim.file.LogisimFile;
import com.cburch.logisim.instance.Instance;
import com.cburch.logisim.instance.InstanceState;
import com.cburch.logisim.proj.Project;
import com.cburch.logisim.std.wiring.Pin;

/**
 * Runs test vectors against circuits using Logisim's own simulation engine.
 * Usage: java -cp logisim.jar;. LogiTest file.circ vectors.txt
 * Vector file:  CIRCUIT name / IN a b / OUT x y / ROW 0 1 | 1 x / END
 * Rows run in order on one circuit state, so sequential tests work too.
 */
public class LogiTest {
    public static void main(String[] args) throws Exception {
        LogisimFile file = new Loader(null).openLogisimFile(new File(args[0]));
        Project proj = new Project(file);
        BufferedReader in = new BufferedReader(new FileReader(args[1]));
        String line, name = null;
        List<String> ins = null, outs = null;
        List<String[]> rows = new ArrayList<String[]>();
        int pass = 0, fail = 0;
        while ((line = in.readLine()) != null) {
            line = line.trim();
            if (line.startsWith("CIRCUIT ")) { name = line.substring(8); rows.clear(); }
            else if (line.startsWith("IN")) ins = split(line.substring(2));
            else if (line.startsWith("OUT")) outs = split(line.substring(3));
            else if (line.startsWith("ROW ")) rows.add(line.substring(4).split("\\|"));
            else if (line.equals("END")) {
                String r = run(proj, file, name, ins, outs, rows);
                if (r == null) { pass++; System.out.println("PASS " + name); }
                else { fail++; System.out.println("FAIL " + name + " :: " + r); }
            }
        }
        System.out.println("TOTAL pass=" + pass + " fail=" + fail);
        System.exit(0);
    }

    static List<String> split(String s) {
        List<String> r = new ArrayList<String>();
        for (String t : s.trim().split("\\s+")) if (t.length() > 0) r.add(t);
        return r;
    }

    static String run(Project proj, LogisimFile file, String name, List<String> ins,
                      List<String> outs, List<String[]> rows) {
        Circuit circ = file.getCircuit(name);
        if (circ == null) return "circuit not found";
        Map<String, Instance> pins = new HashMap<String, Instance>();
        for (com.cburch.logisim.comp.Component comp : circ.getNonWires()) {
            if (comp.getFactory() instanceof Pin) {
                String lab = comp.getAttributeSet().getValue(com.cburch.logisim.instance.StdAttr.LABEL);
                pins.put(lab, Instance.getInstanceFor(comp));
            }
        }
        for (String p : ins) if (!pins.containsKey(p)) return "missing input pin " + p + " have " + pins.values();
        for (String p : outs) if (!pins.containsKey(p)) return "missing output pin " + p + " have " + pins.values();
        CircuitState st = new CircuitState(proj, circ);
        Propagator prop = st.getPropagator();
        prop.propagate();
        StringBuilder err = new StringBuilder();
        int bad = 0, rowNo = 0;
        for (String[] row : rows) {
            rowNo++;
            List<String> iv = split(row[0]);
            List<String> ov = split(row.length > 1 ? row[1] : "");
            for (int i = 0; i < ins.size(); i++) {
                InstanceState ps = st.getInstanceState(pins.get(ins.get(i)));
                Pin.FACTORY.setValue(ps, iv.get(i).equals("1") ? Value.TRUE : Value.FALSE);
                ps.fireInvalidated();
            }
            prop.propagate();
            if (prop.isOscillating()) return "OSCILLATION at row " + rowNo;
            for (int i = 0; i < outs.size(); i++) {
                String want = ov.get(i);
                if (want.equals("x")) continue;
                Value v = Pin.FACTORY.getValue(st.getInstanceState(pins.get(outs.get(i))));
                String got = v == Value.TRUE ? "1" : v == Value.FALSE ? "0" : v.toString();
                if (!got.equals(want)) {
                    bad++;
                    if (bad <= 4) err.append("row" + rowNo + "[" + row[0].trim() + "] " + outs.get(i)
                            + " want " + want + " got " + got + "; ");
                }
            }
        }
        return bad == 0 ? null : bad + " mismatches: " + err;
    }
}
