package lk.ac.mrt.fit.library_api.service;

import java.util.List;
import java.util.Optional;
import lk.ac.mrt.fit.library_api.model.Book;
import lk.ac.mrt.fit.library_api.repository.BookRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
public class BookService {
    private final BookRepository bookRepository;

    public BookService(BookRepository bookRepository) {
        this.bookRepository = bookRepository;
    }

    @Transactional(readOnly = true)
    public List<Book> getAllBooks() {
        return bookRepository.findAll();
    }

    @Transactional(readOnly = true)
    public Optional<Book> getBookById(Long id) {
        return bookRepository.findById(id);
    }

    public Book createBook(Book book) {
        // A POST always creates a new row; clients cannot choose an existing id.
        book.setId(null);
        return bookRepository.save(book);
    }

    public Optional<Book> updateBook(Long id, Book details) {
        return bookRepository.findById(id).map(book -> {
            book.setTitle(details.getTitle());
            book.setAuthor(details.getAuthor());
            book.setIsbn(details.getIsbn());
            book.setPrice(details.getPrice());
            return bookRepository.save(book);
        });
    }

    public boolean deleteBook(Long id) {
        return bookRepository.findById(id).map(book -> {
            bookRepository.delete(book);
            return true;
        }).orElse(false);
    }
}
