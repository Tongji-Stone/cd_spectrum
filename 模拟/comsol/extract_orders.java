import com.comsol.model.*;
import com.comsol.model.util.*;

public class extract_orders {
  public static void main(String[] args) throws Exception {
    ModelUtil.clear();
    String mph = "C:/Users/qiann/Desktop/TJPT光栅/模拟/comsol/wave_grating_cell_Model.mph";
    Model model = ModelUtil.load("m", mph);

    // List physics feature tags under ewfd and under ps1/pport1
    String[] top = model.component("comp1").physics("ewfd").feature().tags();
    StringBuilder sb1 = new StringBuilder("EWFD_TAGS:");
    for (String t : top) sb1.append(" ").append(t);

    String[] sub = model.component("comp1").physics("ewfd").feature("ps1").feature().tags();
    StringBuilder sb2 = new StringBuilder("PS1_TAGS:");
    for (String t : sub) sb2.append(" ").append(t);

    String[] ports = model.component("comp1").physics("ewfd").feature("ps1").feature("pport1").feature().tags();
    StringBuilder sb3 = new StringBuilder("PPORT1_TAGS:");
    for (String t : ports) sb3.append(" ").append(t);

    // Write via a result table export (allowed) - put tags into a table cell
    model.result().table().create("tbl1", "Table");
    model.result().table("tbl1").clearTableData();
    model.result().table("tbl1").addRow(new String[]{sb1.toString()});
    model.result().table("tbl1").addRow(new String[]{sb2.toString()});
    model.result().table("tbl1").addRow(new String[]{sb3.toString()});

    model.result().export().create("tbl_exp", "Table");
    model.result().export("tbl_exp").set("table", "tbl1");
    model.result().export("tbl_exp").set("filename",
      "C:/Users/qiann/Desktop/TJPT光栅/模拟/comsol/tags.txt");
    model.result().export("tbl_exp").run();
  }
}
