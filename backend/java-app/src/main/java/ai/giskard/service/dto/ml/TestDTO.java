package ai.giskard.service.dto.ml;

import ai.giskard.domain.ml.CodeLanguage;
import ai.giskard.domain.ml.TestResult;
import ai.giskard.domain.ml.TestType;
import ai.giskard.domain.ml.testing.Test;
import ai.giskard.domain.ml.testing.TestExecution;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.validation.constraints.NotNull;
import java.util.Date;

@Setter
@Getter
@NoArgsConstructor
public class TestDTO {
    private Long id;

    @NotNull
    private String name;

    private String code;

    private CodeLanguage language;

    private Long suiteId;

    private TestType type;

    private TestResult status;
    private Date lastExecutionDate;

    public TestDTO(Test test) {
        id = test.getId();
        name = test.getName();
        code = test.getCode();
        language = test.getLanguage();
        suiteId = test.getTestSuite().getId();
        type = test.getType();
    }
}
