package lk.ac.mrt.fit.library_api;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.info.Info;

@SpringBootApplication
@OpenAPIDefinition(info = @Info(title = "Library API", version = "1.0",
        description = "IN3101 Lab 02 - Suthankan Balenthiran - 234202J"))
public class LibraryApiApplication {
    public static void main(String[] args) {
        SpringApplication.run(LibraryApiApplication.class, args);
    }
}
