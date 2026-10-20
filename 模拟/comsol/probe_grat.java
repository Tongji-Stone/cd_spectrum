import com.comsol.model.*;
import com.comsol.model.util.*;

public class probe_grat {
  public static void main(String[] args) throws Exception {
    ModelUtil.clear();
    Model model = ModelUtil.load("m",
      "C:/Users/qiann/Desktop/TJPT光栅/模拟/comsol/ray_ring_3d_Model.mph");
    String[] props = model.component("comp1").physics("gop").feature("grat1").properties();
    // Stuff all property names into the model description; then export it.
    StringBuilder sb = new StringBuilder();
    for (String p : props) sb.append(p).append("\n");
    model.description(sb.toString());
    // write description into a table via a single global eval of a string param is hard;
    // instead create a text export through an Image is overkill. Use a result "table" file.
    model.result().table().create("tbl1", "Table");
    model.result().table("tbl1").comments(sb.toString());
    model.result().export().create("texp", "Table");
    model.result().export("texp").set("table", "tbl1");
    model.result().export("texp").set("filename",
      "C:/Users/qiann/Desktop/TJPT光栅/模拟/comsol/grat_props.txt");
    model.result().export("texp").run();
  }
}
