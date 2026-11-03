package lk.ac.mrt.fit.library_api.model;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.PositiveOrZero;
import io.swagger.v3.oas.annotations.media.Schema;

@Entity
public class Book {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Schema(accessMode = Schema.AccessMode.READ_ONLY, example = "1")
    private Long id;

    @NotBlank
    @Schema(example = "234202J - Clean Code")
    private String title;

    @NotBlank
    @Schema(example = "Robert C. Martin")
    private String author;

    @Schema(example = "9780132350884")
    private String isbn;

    @PositiveOrZero
    @Schema(example = "4500.00")
    private Double price;

    public Book() {
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public String getAuthor() { return author; }
    public void setAuthor(String author) { this.author = author; }
    public String getIsbn() { return isbn; }
    public void setIsbn(String isbn) { this.isbn = isbn; }
    public Double getPrice() { return price; }
    public void setPrice(Double price) { this.price = price; }
}
